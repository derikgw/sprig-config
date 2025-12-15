# The AI mentioned the loader handling format specific imports.

Perfect. Here is the **direct, lossless JSON equivalent** of your `application.yml`.

No restructuring, no normalization, no “helpful” changes.

---

## `application.json`

```json
{
  "app": {
    "name": "SprigTestApp",
    "profile": "base"
  },
  "logging": {
    "level": "INFO",
    "format": "%(message)s"
  },
  "etl": {
    "jobs": {
      "root": "/jobs/default",
      "default_shell": "/bin/bash",
      "repositories": {
        "inmemory": {
          "class": "InMemoryJobRepo",
          "params": {
            "x": 1
          }
        }
      }
    }
  },
  "imports": [
    "imports/job-default.yml",
    "imports/common.yml"
  ]
}
```

---

## Parity check (important but brief)

✔ No YAML-only features used
✔ No anchors / aliases
✔ No implicit booleans
✔ No multi-line scalars
✔ Strings explicitly preserved
✔ Paths remain strings
✔ List semantics preserved

This file should produce **the exact same in-memory structure** after parsing.

---

## One subtle thing worth noting (not a blocker)

You’re already doing something *good* here:

```yaml
imports:
  - imports/job-default.yml
```

JSON doesn’t care, but **your loader might eventually** if you later support:

* format-specific imports (`.json`, `.toml`)
* or extension filtering

Right now, this is totally fine — just flagging it as a future design seam, not an issue.

---

Whenever you’re ready, paste the **next YAML file** and we’ll keep converting.
