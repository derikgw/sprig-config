# Contributing to SprigConfig

Thank you for your interest in contributing to **SprigConfig**.

SprigConfig aims to provide **predictable, debuggable, Spring-style configuration composition for Python**, with a strong emphasis on clarity over cleverness.

Before opening an issue or pull request, please read the principles below.

---

## Guiding Principles

These principles are **non-negotiable** and guide all design decisions:

1. **Config behavior > file format**
2. **Parsing is a leaf concern**
3. **Backward compatibility is sacred in 1.x**
4. **2.0 only when contracts change**

If a change violates one of these, it is either deferred or requires a major version bump.

---

## Supported Configuration Formats

SprigConfig currently supports:

- **YAML**
- **JSON**

These formats were chosen because they **natively express hierarchical configuration**, which allows merge semantics to remain explicit and debuggable.

### About `.properties`, INI, and similar formats

Flat formats (e.g. `.properties`, `.ini`) do not natively express structure and require invented behavior such as:

- dot-splitting
- implicit hierarchy
- list coercion
- type inference rules

For this reason, these formats are **not supported by default**.

Support may be considered if:
- there is demonstrated real-world demand
- semantics are explicit and well-documented
- behavior does not silently alter merge or provenance rules

Forking or experimental extensions are encouraged if you wish to explore this space.

---

## Issues

When opening an issue, please include:

- What you expected to happen
- What actually happened
- Relevant config snippets (redacted if needed)
- Whether the issue affects backward compatibility

Feature requests should explain the **problem**, not just the solution.

---

## Pull Requests

Pull requests should:

- Preserve existing behavior unless explicitly discussed
- Include tests for new behavior
- Avoid introducing format-specific logic into merge or core loader paths
- Respect existing naming and structure conventions

Large changes should be discussed in an issue before implementation.

---

## Development Philosophy

SprigConfig favors:

- Explicit behavior over magic
- Deterministic merges over convenience
- Traceability over minimalism

If in doubt, choose the option that makes configuration behavior easier to **reason about at 3am during an outage**.

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
