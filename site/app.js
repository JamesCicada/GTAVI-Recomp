// Renders progress.json, written by scripts/update_progress.py --site.
"use strict";

const fmt = new Intl.NumberFormat("en-US");

function pct(part, whole) {
  return whole ? Math.round((100 * part) / whole) : 0;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// segments: [{kind: "done" | "open" | "blocked", value}]
function bar(segments, label) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);
  const done = segments.find((s) => s.kind === "done")?.value ?? 0;
  const node = el("div", "bar");
  node.setAttribute("role", "progressbar");
  node.setAttribute("aria-valuemin", "0");
  node.setAttribute("aria-valuemax", String(total));
  node.setAttribute("aria-valuenow", String(done));
  node.setAttribute("aria-label", label);
  for (const s of segments) {
    if (!s.value || s.kind === "open") continue;
    const part = el("span", s.kind);
    part.style.width = total ? `${(100 * s.value) / total}%` : "0";
    // Push blocked work to the right end, after the open gap.
    if (s.kind === "blocked") part.style.marginLeft = "auto";
    node.append(part);
  }
  return node;
}

function row({ title, sub, done, total, blocked = 0, extra, className }) {
  const li = el("li", className ? `row ${className}` : "row");
  const label = el("div", "row-label");
  label.append(el("span", "row-title", title));
  if (sub) label.append(el("span", "row-sub", sub));

  const figure = el("div", "row-figure");
  figure.append(el("strong", "", `${pct(done, total)}%`));
  figure.append(el("small", "", extra ?? `${fmt.format(done)} / ${fmt.format(total)}`));

  li.append(
    label,
    figure,
    bar(
      [
        { kind: "done", value: done },
        { kind: "open", value: total - done - blocked },
        { kind: "blocked", value: blocked },
      ],
      `${title}: ${fmt.format(done)} of ${fmt.format(total)} done`,
    ),
  );
  return li;
}

function stat(value, label, done, total) {
  const li = el("li", "stat");
  li.append(el("div", "stat-value", value), el("div", "stat-label", label));
  if (total) {
    li.append(bar([{ kind: "done", value: done }, { kind: "open", value: total - done }], label));
  }
  return li;
}

function render(data) {
  const roadmap = data.roadmap;
  const tasks = roadmap.done + roadmap.open + roadmap.blocked;
  const up = data.anyps5;
  const rdna2 = up.shaders.rdna2;
  const gfx1013 = up.shaders.gfx1013;

  document.querySelector('[data-fill="blocked"]').textContent = fmt.format(roadmap.blocked);
  document.querySelector('[data-fill="tasks"]').textContent = fmt.format(tasks);

  document.getElementById("stats").append(
    stat(`${pct(roadmap.done, tasks)}%`, "Roadmap tasks done", roadmap.done, tasks),
    stat(`${pct(rdna2.translated, rdna2.total)}%`, "Shaders translated (RDNA 2)", rdna2.translated, rdna2.total),
    stat(`${pct(up.libraries.done, up.libraries.total)}%`, "System library functions", up.libraries.done, up.libraries.total),
    stat(fmt.format(roadmap.blocked), "Tasks waiting on game files"),
  );

  const phases = document.getElementById("phases");
  for (const p of roadmap.phases) {
    const total = p.done + p.open + p.blocked;
    phases.append(
      row({
        title: `${p.number}. ${p.title}`,
        done: p.done,
        total,
        blocked: p.blocked,
        extra: `${p.done} / ${total}` + (p.blocked ? ` · ${p.blocked} blocked` : ""),
      }),
    );
  }
  phases.append(
    row({
      title: "Overall",
      done: roadmap.done,
      total: tasks,
      blocked: roadmap.blocked,
      extra: `${roadmap.done} / ${tasks} · ${roadmap.blocked} blocked`,
      className: "total",
    }),
  );

  document.getElementById("shaders").append(
    row({ title: `${rdna2.isa} reference`, sub: "instruction forms translated", done: rdna2.translated, total: rdna2.total }),
    row({ title: gfx1013.isa, sub: "instruction forms translated", done: gfx1013.translated, total: gfx1013.total }),
  );
  document.getElementById("shader-note").textContent =
    `A translated instruction means the recompiler handles it, not that the result has been verified on a game. ` +
    `The recompiler still has ${fmt.format(up.shaders.unsupported_throws)} code paths that report an unsupported case.`;

  const libraries = document.getElementById("libraries");
  libraries.append(
    row({
      title: `All system libraries`,
      sub: `${fmt.format(up.library_count)} libraries`,
      done: up.libraries.done,
      total: up.libraries.total,
      className: "total-first",
    }),
  );
  for (const lib of up.core_libraries) {
    libraries.append(row({ title: lib.role, sub: lib.name, done: lib.done, total: lib.total }));
  }

  const provenance = document.getElementById("provenance");
  provenance.textContent = "Library and shader counts measured by AnyPS5's tools/progress.py at commit ";
  const link = el("a", "", up.commit.slice(0, 7));
  link.href = up.source;
  provenance.append(link, ". Roadmap counts come from TODO.md.");
}

fetch("progress.json", { cache: "no-cache" })
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then(render)
  .catch((error) => {
    const box = document.getElementById("error");
    box.hidden = false;
    box.textContent = `Progress data could not be loaded (${error.message}).`;
    document.getElementById("provenance").textContent = "";
  });
