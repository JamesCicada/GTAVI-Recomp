"""Inspect the readable PS5 application inputs needed before relinking."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct


ELF_HEADER = struct.Struct("<16sHHIQQQIHHHHHH")
PROGRAM_HEADER = struct.Struct("<IIQQQQQQ")
SELF_MAGIC = (b"\x54\x14\xf5\xee", b"\x4f\x15\x3d\x1d")
MAX_PARAM_BYTES = 1024 * 1024


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate metadata field {name!r}")
        result[name] = value
    return result


def read_param(path, expected_title, expected_version, expected_content=None):
    with path.open("rb") as stream:
        raw = stream.read(MAX_PARAM_BYTES + 1)
    if len(raw) > MAX_PARAM_BYTES:
        raise ValueError("metadata exceeds the size limit")
    data = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=unique_object)
    if not isinstance(data, dict):
        raise ValueError("metadata must be a JSON object")
    title = data.get("titleId")
    version = data.get("contentVersion")
    if not isinstance(title, str) or not re.fullmatch(r"PPSA[0-9]{5}", title):
        raise ValueError("metadata needs a PS5 titleId")
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]{2}\.[0-9]{3}\.[0-9]{3}", version):
        raise ValueError("metadata needs a contentVersion formatted as NN.NNN.NNN")
    if expected_title and title != expected_title:
        raise ValueError(f"title ID is {title}, expected {expected_title}")
    if expected_version and version != expected_version:
        raise ValueError(f"content version is {version}, expected {expected_version}")
    content = data.get("contentId")
    if expected_content is not None and content != expected_content:
        raise ValueError(f"content ID is {content!r}, expected {expected_content!r}")
    result = {"title_id": title, "content_version": version, "sha256": hashlib.sha256(raw).hexdigest()}
    if isinstance(content, str):
        result["content_id"] = content
    return result


def read_elf(path, *, module=False):
    role = "shared module" if module else "executable"
    allowed_types = (3, 0xFE18) if module else (2, 3, 0xFE10)
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        header = stream.read(ELF_HEADER.size)
        if header[:4] in SELF_MAGIC:
            raise ValueError(f"found a SELF container; supply a readable ELF {role}")
        if len(header) != ELF_HEADER.size or header[:7] != b"\x7fELF\x02\x01\x01":
            raise ValueError(f"expected a little-endian 64-bit ELF {role}")
        _, kind, machine, version, entry, phoff, _, _, ehsize, phsize, count, _, _, _ = ELF_HEADER.unpack(header)
        if machine != 62 or version != 1 or kind not in allowed_types:
            raise ValueError(f"expected an x86-64 ELF {role}")
        if (ehsize != ELF_HEADER.size or phsize != PROGRAM_HEADER.size or not count
                or phoff < ehsize or phoff + count * phsize > before.st_size):
            raise ValueError("invalid program-header table")
        stream.seek(phoff)
        entry_present = False
        file_data_present = False
        for _ in range(count):
            raw = stream.read(phsize)
            if len(raw) != phsize:
                raise ValueError("program-header table is truncated")
            segment_type, flags, offset, address, _, stored, memory, _ = PROGRAM_HEADER.unpack(raw)
            if segment_type != 1:
                continue
            if stored > memory or offset + stored > before.st_size or address + memory > 1 << 64:
                raise ValueError("invalid load segment")
            file_data_present |= stored > 0
            entry_present |= bool(flags & 1) and address <= entry < address + stored
        if module and not file_data_present:
            raise ValueError("shared module has no file-backed load segment")
        if not module and not entry_present:
            raise ValueError("entry point is outside the executable file-backed segments")
        stream.seek(0)
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError(f"{role} changed during inspection")
    return {"bytes": before.st_size, "sha256": digest}


def check_app0(directory, title=None, version=None, modules=(), *, content_id=None):
    report = {"app0": str(directory), "metadata": None, "executable": None, "errors": {}}
    if modules:
        report["modules"] = {f"sce_module/{name}": None for name in modules}
    if not directory.is_dir():
        report["errors"]["app0"] = "expected an application directory"
        return report
    try:
        report["metadata"] = read_param(directory / "sce_sys/param.json", title, version, content_id)
    except RecursionError:
        report["errors"]["sce_sys/param.json"] = "metadata is nested too deeply"
    except (OSError, ValueError) as error:
        report["errors"]["sce_sys/param.json"] = str(error)
    try:
        report["executable"] = read_elf(directory / "eboot.bin")
    except (OSError, ValueError) as error:
        report["errors"]["eboot.bin"] = str(error)
    for relative_path in report.get("modules", {}):
        try:
            report["modules"][relative_path] = read_elf(directory / relative_path, module=True)
        except (OSError, ValueError) as error:
            report["errors"][relative_path] = str(error)
    return report


def module_name(value):
    if not re.fullmatch(r"[a-zA-Z0-9_][a-zA-Z0-9_.-]*\.prx", value, re.IGNORECASE):
        raise argparse.ArgumentTypeError("expected a .prx basename under sce_module")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app0", type=Path, help="user-supplied application directory")
    parser.add_argument("--title-id", help="expected title ID")
    parser.add_argument("--content-id", help="expected full package content ID")
    parser.add_argument("--content-version", help="expected content version")
    parser.add_argument("--module", action="append", type=module_name, default=[],
                        help="require a readable .prx in sce_module (repeatable)")
    args = parser.parse_args(argv)
    report = check_app0(args.app0, args.title_id, args.content_version, args.module, content_id=args.content_id)
    print(json.dumps(report, indent=2))
    return 2 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
