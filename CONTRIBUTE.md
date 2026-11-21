# Contributing

Thank you for your interest in contributing to the GTA VI Translation Layer.

This project aims to build a translation layer that lets the PlayStation 5 build
of Grand Theft Auto VI run natively on PC (Windows and Linux) by translating the
system libraries it depends on. See
[docs/adr/0002-ps5-to-pc-library-translation.md](docs/adr/0002-ps5-to-pc-library-translation.md).

We welcome contributions from developers, reverse engineers, researchers, testers, documentation writers, and AI-assisted development agents.

Our goal is to make contributing straightforward, collaborative, and efficient.

## Ways to Contribute

There are several ways to help the project:

- **Development:** Implement translation mechanisms, platform integrations, and runtime components.
- **Research:** Investigate game dependencies, executable structures, operating system behavior, and compatibility requirements.
- **Testing:** Test implemented functionality and report reproducible bugs.
- **Documentation:** Improve technical documentation, architecture explanations, and installation instructions.
- **Optimization:** Identify performance bottlenecks and suggest improvements.
- **Code Review:** Review pull requests, identify potential issues, and suggest improvements.

You don't need to be an expert in every area. Contributions of any size are welcome.

## AI Agents Are Welcome

AI coding agents are explicitly allowed and encouraged to contribute to this project.

We recognize that AI agents can significantly speed up research, implementation, debugging, testing, and documentation.

Contributors may use tools such as:

- OpenAI Codex
- Claude Code
- GitHub Copilot
- Cursor
- Gemini CLI
- Other autonomous or assisted development agents

There are no restrictions on which coding agent you use, provided the contribution follows the project's technical and licensing requirements.

### Guidelines for AI-Assisted Contributions

AI-generated code is treated like any other contribution and must meet the same quality standards.

Contributors and agents should:

1. Understand the purpose of the changes being submitted.
2. Follow the existing project architecture and coding conventions.
3. Avoid inventing APIs, undocumented behavior, or compatibility claims.
4. Include appropriate tests where applicable.
5. Document assumptions and known limitations.
6. Avoid introducing unnecessary dependencies.
7. Ensure that generated code does not violate third-party licenses.
8. Never include proprietary game files, copyrighted assets, PS5 system files,
   decryption keys, or leaked source code.

**Human review is welcome but does not need to become a bottleneck.** Small, well-scoped contributions with clear explanations and passing tests should be straightforward to merge.

### Agent-Specific Instructions

Agents working on this repository should:

- Read `README.md`, `TODO.md`, and this document before starting.
- Inspect the existing codebase before proposing architectural changes.
- Check existing issues and pull requests to avoid duplicate work.
- Work on clearly defined tasks.
- Keep changes focused and avoid unrelated refactoring.
- Build and run the test suite before submitting (see `docs/build.md`).
- Report anything that cannot be verified.
- Provide a concise summary of modifications and testing results.

Agents may independently research, implement, test, and submit changes without requiring prior approval for every individual task.

However, destructive changes, major architectural decisions, and changes that affect project-wide interfaces should be discussed before implementation.

## Making Contributions Quickly

We want to minimize unnecessary bureaucracy.

For small fixes and improvements, contributors can submit a pull request directly.

For larger features, we recommend opening an issue first so that implementation details can be discussed and overlapping work can be avoided.

### Suggested Workflow

1. Fork the repository.
2. Clone your fork.
3. Create a feature branch.
4. Implement your changes.
5. Run relevant tests.
6. Commit your changes.
7. Open a pull request against the main repository.

Example:

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY

git checkout -b feature/my-feature

# Make your changes

git add .
git commit -m "feat: implement my feature"
git push origin feature/my-feature
```

## Pull Request Guidelines

To help us review contributions quickly, please include:

- A clear description of what was changed.
- The reason for the change.
- Relevant issues or discussions.
- Testing performed.
- Known limitations or outstanding problems.

For AI-assisted contributions, mentioning the agent used is appreciated but not mandatory.

### Pull Request Size

We prefer focused pull requests.

Examples:

- Fixing a filesystem translation issue.
- Adding support for a specific API.
- Improving error handling.
- Adding a missing test.
- Updating technical documentation.

Large pull requests are welcome when the feature genuinely requires them, but should be broken into smaller changes whenever practical.

## Coding Standards

- Use the project's selected C++ standard.
- Prefer modern C++ practices.
- Use RAII for resource management.
- Avoid unnecessary raw memory ownership.
- Keep platform-specific implementations isolated.
- Use descriptive names and meaningful comments.
- Handle errors explicitly.
- Avoid unexplained hardcoded values.
- Write tests for new functionality where practical.

Formatting is defined by `.clang-format`; run `clang-format -i` on the C++ files
you change. The build enables a strict warning set (see
`cmake/CompilerWarnings.cmake`) and CI builds with warnings treated as errors.
Build and test instructions are in [docs/build.md](docs/build.md).

## Research Contributions

Research is particularly valuable for this project.

If you discover something relevant to compatibility, please provide:

- A description of the finding.
- Relevant documentation or references.
- Reproduction steps where applicable.
- Technical implications.
- Potential implementation approaches.

Clearly distinguish confirmed findings from hypotheses.

## Bug Reports

When reporting a bug, include:

- Operating system and version.
- Hardware specifications where relevant.
- Build or commit version.
- Steps to reproduce.
- Expected behavior.
- Actual behavior.
- Relevant logs or error messages.

Avoid including proprietary game files or sensitive information in reports.

## Communication

Please keep discussions constructive and technical.

We encourage contributors to ask questions, suggest alternative approaches, challenge architectural decisions, and share research.

The objective is to solve problems, not create unnecessary barriers to participation.

## Licensing & Legal Considerations

The project is licensed under the [MIT License](LICENSE). By contributing, you agree that your submissions are licensed under it and must be legally permissible to distribute under it.

Do not submit:

- Proprietary GTA VI game files.
- Leaked Rockstar Games source code.
- Copyrighted game assets.
- Sony proprietary code, SDK material, or PS5 system libraries.
- Decryption keys, entitlements, or licence data.
- Material obtained by bypassing protection mechanisms.
- Proprietary third-party code without appropriate licensing.
- Credentials, private keys, or other sensitive information.

Reverse engineering and interoperability research must be conducted in accordance with applicable laws.

## Final Note

This project is community-driven.

Whether you're an experienced systems programmer, a reverse engineer, a researcher, a tester, or an AI coding agent, your contributions are welcome.

**Our priority is making meaningful progress without making the contribution process unnecessarily complicated.**

Research, build, test, document, and collaborate. Let's make cross-platform compatibility a reality.
