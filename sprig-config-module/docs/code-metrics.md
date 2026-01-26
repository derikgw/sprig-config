# Code Metrics and Quality Analysis

This document describes how to use code quality and metrics tools to analyze the SprigConfig codebase.

## Table of Contents

- [Radon - Code Complexity & Metrics](#radon---code-complexity--metrics)
- [Available Metrics](#available-metrics)
- [Interpreting Results](#interpreting-results)
- [Best Practices](#best-practices)

---

## Radon - Code Complexity & Metrics

**Radon** is a Python tool that analyzes code quality by measuring lines of code, cyclomatic complexity, and maintainability.

### Installation

Radon is already included in the dev dependencies. No additional setup needed.

### Running Radon

#### Get Lines of Code Statistics

```bash
cd sprig-config-module

# Show lines of code breakdown by file
poetry run radon raw src
```

**Example Output:**
```
src/sprigconfig/__init__.py
  LOC: 5
  LLOC: 3
  SLOC: 5
  Comments: 0
  Multi-line strings: 0
  Blank lines: 0

src/sprigconfig/config.py
  LOC: 250
  LLOC: 180
  SLOC: 240
  Comments: 15
  Multi-line strings: 20
  Blank lines: 10

...
```

#### Analyze Cyclomatic Complexity

```bash
# Show function/method complexity
poetry run radon cc src

# Detailed view (recommended)
poetry run radon cc src -s

# Show only functions with high complexity
poetry run radon cc src --min B
```

**Complexity Levels:**
- `A`: Simple function (score 1-5)
- `B`: Moderate (score 6-10)
- `C`: Slightly complex (score 11-20)
- `D`: Complex (score 21-30)
- `E`: Very complex (score 31-40)
- `F`: Extremely complex (score >40) ⚠️

#### Maintainability Index

```bash
# Get overall code quality score (0-100)
poetry run radon mi src

# Verbose output with breakdown
poetry run radon mi src -s
```

**Score Interpretation:**
- `100-20`: Good maintainability (Green ✅)
- `19-10`: Medium maintainability (Yellow ⚠️)
- `<10`: Low maintainability (Red 🔴)

---

## Available Metrics

### LOC (Lines of Code)
- **Physical LOC**: All lines including blanks and comments
- **LLOC (Logical)**: Actual code lines (what you usually care about)
- **SLOC (Source)**: Code lines excluding docstrings
- **Blank lines**: Empty lines
- **Comments**: Comment-only lines

### Cyclomatic Complexity (CC)
Measures how many independent paths exist through code. Higher = more complex.

**Example:**
```python
# CC = 1 (simple, straightforward)
def add(a, b):
    return a + b

# CC = 3 (has 3 branches)
def validate(value):
    if value < 0:
        return False
    elif value > 100:
        return False
    else:
        return True
```

### Maintainability Index (MI)
A composite metric combining:
- Lines of code
- Cyclomatic complexity
- Halstead volume
- Comments ratio

Higher score = easier to maintain.

---

## Interpreting Results

### What to Look For

1. **High Complexity Functions** (CC > D)
   - Consider refactoring into smaller functions
   - Break logic into helper methods
   - Simplify conditional branches

2. **Large Files** (LLOC > 300)
   - May indicate multiple responsibilities
   - Consider splitting into focused modules

3. **Low Maintainability Score** (MI < 20)
   - Code is hard to understand/modify
   - Prioritize for refactoring
   - Add more tests and documentation

4. **Low Comment Ratio**
   - Complex logic without explanation
   - Add docstrings to public functions
   - Comment non-obvious algorithms

### Practical Example

```bash
# Find all functions with complexity >= C
poetry run radon cc src --min C

# Output shows:
# src/sprigconfig/deepmerge.py
#     merge_dicts F:42:4 - 25 (Very Complex)
#     ^ This function needs refactoring!
```

---

## Best Practices

### 1. Aim for Simple Functions

```bash
# Regularly check complexity
poetry run radon cc src -s

# Target: Most functions should be A or B
# Never ignore F-level complexity
```

### 2. Document Complex Logic

If a function has high complexity, add docstrings:

```python
def process_config(config, profile):
    """
    Complex config processing with multiple branches.

    Args:
        config: Configuration dict
        profile: Profile name (dev/test/prod)

    Returns:
        Processed config dict

    Raises:
        ConfigError: If validation fails
    """
    # Implementation...
```

### 3. Monitor Code Quality Trends

```bash
# Keep a log of metrics
poetry run radon mi src > metrics_baseline.txt

# After major refactoring
poetry run radon mi src > metrics_new.txt

# Compare
diff metrics_baseline.txt metrics_new.txt
```

### 4. Use with Code Review

During code review, check:

```bash
# Show only added/modified files
poetry run radon cc src/sprigconfig/new_module.py -s
```

If new code has high complexity, request refactoring during review.

### 5. CI/CD Integration

Before committing complex code:

```bash
# Check metrics locally
poetry run radon cc src --min C
poetry run radon mi src

# If either is concerning, refactor before pushing
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `poetry run radon raw src` | Lines of code breakdown |
| `poetry run radon cc src` | Cyclomatic complexity |
| `poetry run radon cc src -s` | CC with detailed summary |
| `poetry run radon cc src --min C` | Show only complex functions |
| `poetry run radon mi src` | Maintainability index |
| `poetry run radon mi src -s` | MI with detailed breakdown |
| `poetry run radon cc src --show-closures` | Include nested functions |

---

## Related Documentation

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Code standards and guidelines
- [dependency-management.md](./dependency-management.md) - Managing dependencies
- [README_Developer_Guide.md](./README_Developer_Guide.md) - General developer guide

---

## External Resources

- [Radon Documentation](https://radon.readthedocs.io/)
- [Cyclomatic Complexity Explained](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Code Quality Best Practices](https://refactoring.guru/refactoring)
