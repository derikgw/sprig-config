# SprigConfig Configuration Rules

This document describes how the system should interpret and process configuration files using `sprigconfig`. The rules below define how base configs, profile overlays, and imports should be handled to generate a final configuration structure.

## 1. YAML Structure Used As-Is
Every key in YAML files is interpreted literally. Keys such as `app:` are not treated specially. They follow the same merge rules as any other key.

## 2. Deep Merge Behavior
- **Mapping + Mapping** → deep-merged recursively  
- **List + List** → lists are overwritten by the later value  
- **Scalar + Scalar** → overwritten by the later value  

## 3. Merge Order (Final Precedence)
1. `application.yml`  
2. Imports from `application.yml` (recursive)  
3. `application-<profile>.yml`  
4. Imports from `application-<profile>.yml` (recursive)  

## 4. Handling of Imports
Only the YAML files listed via `imports:` are included. Other files are ignored.

## 5. Profile Files
The system recognizes any file named using:
```
application-<profile>.yml
```
The runtime profile selects which of these files is loaded.

## 6. Metadata Injection
SprigConfig adds a `_meta` object under the `sprigconfig:` root to track:
- The runtime profile used to generate the config
- The list of all files that were merged in order

Example:
```
sprigconfig:
  _meta:
    profile: dev
    files:
      - application.yml
      - application-dev.yml
      - imports/common.yml
```

This `_meta` data is the only extra information added by SprigConfig. The rest of the configuration is strictly a result of merging YAML files.
