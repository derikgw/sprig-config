# Documentation for `tests/test_cli.py`

This document explains the purpose and functionality of the CLI integration
tests found in:

```
tests/test_cli.py
```

These tests validate the command‑line interface for SprigConfig, ensuring that
the CLI behaves correctly when invoked as a subprocess and that configuration
output is accurate.

---

# 🎯 Purpose of `test_cli.py`

The SprigConfig CLI provides a user‑facing way to:

- Load configuration files  
- Merge base and profile layers  
- Resolve imports  
- Format output in YAML or JSON  
- Write merged config to stdout or a file  

These tests verify that the CLI behaves correctly in an environment that mimics
real shell usage.

Because the CLI runs in a **separate process**, these tests use `subprocess.Popen`
to capture its exit code, stdout, and stderr exactly as a user would see them.

---

# 🧪 1. Autouse Fixture: `disable_logging_handlers`

```python
@pytest.fixture(autouse=True)
def disable_logging_handlers():
```

### Purpose:
Ensures that when the CLI runs as a subprocess, **no logging handlers bleed into
stdout or stderr**.

The fixture:

- Removes global logging handlers before each test  
- Restores them after the test  

### Why this matters:
The CLI’s output must be **clean YAML/JSON**, with **no logging noise**, so that
the output can be piped into tools like `cat`, `jq`, or other scripts.

---

# ⚙️ 2. Helper Function: `run_cli(args, cwd)`

This function launches the CLI via:

```
python -m sprigconfig.cli …
```

It returns:

```
(rc, stdout, stderr)
```

where:

- `rc` → process exit code  
- `stdout` → main CLI output  
- `stderr` → error messages  

This isolates tests from the Python environment and replicates real command‑line
usage.

---

# 📝 3. Test: `test_cli_dump_basic`

This test validates the most basic CLI behavior:

### Steps:
1. Write a minimal `application.yml` containing:
   ```yaml
   app:
     name: test-app
   ```

2. Run:
   ```
   sprigconfig dump --config-dir <tmp> --profile dev
   ```

3. Assert that:
   - Exit code is `0`  
   - Output contains `app:`  
   - Output contains `name: test-app`  

### What this confirms:
- CLI loads configuration correctly.  
- It prints merged config to stdout.  
- Basic YAML formatting is intact.  

This is a fundamental smoke test for the CLI’s “dump to stdout” mode.

---

# 📝 4. Test: `test_cli_output_file`

This test ensures that the CLI can write merged config to a file using:

```
--output out.yml
```

### Steps:
1. Write:
   ```yaml
   app:
     y: 2
   ```

2. Invoke the CLI with `--output`.

3. Assertions:
   - Exit code is `0`  
   - Output file exists  
   - File contains `y: 2`  

### Why this matters:
This verifies the CLI’s ability to:

- Produce correct merged YAML  
- Handle file output safely  
- Not pollute stdout  

This is critical for scripting, CI automation, and tooling.

---

# ✔️ Summary

These CLI tests ensure:

| Feature | Verified |
|--------|----------|
| Subprocess execution | ✔️ |
| Clean stdout (no logging noise) | ✔️ |
| Correct loading and dumping of YAML | ✔️ |
| Ability to redirect merged output to a file | ✔️ |
| CLI exit codes reflect success or failure | ✔️ |

Security assertions for diagnostic redaction are centralized in
[`security_tests/`](../security_tests/README.md). These functional CLI tests
focus on command behavior and output routing.

## Run

From `sprig-config-module/`:

```bash
poetry run pytest tests/test_cli.py
```
