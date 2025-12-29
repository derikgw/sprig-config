# Building SprigConfig Documentation

This guide explains how to build and preview the SprigConfig documentation locally.

## Prerequisites

The documentation is built using [MkDocs](https://www.mkdocs.org/) with the Material theme and mkdocstrings plugin for API reference generation.

### Install Documentation Dependencies

From the `sprig-config-module/` directory:

```bash
# Install documentation dependencies
poetry install --with docs

# Or if already installed, update
poetry update --with docs
```

This installs:
- `mkdocs` - Documentation site generator
- `mkdocs-material` - Material theme
- `mkdocstrings[python]` - Automatic API reference from docstrings
- `mkdocs-git-revision-date-localized-plugin` - Git-based page dates

## Building the Documentation

### Serve Locally (Development)

To build and serve the documentation with live reload:

```bash
cd sprig-config-module
poetry run mkdocs serve
```

This will:
1. Build the documentation
2. Start a local server at http://127.0.0.1:8000
3. Watch for file changes and auto-reload

**Access the docs:** Open http://127.0.0.1:8000 in your browser

### Build Static Site

To build the static HTML site:

```bash
cd sprig-config-module
poetry run mkdocs build
```

Output will be in `sprig-config-module/site/`

### Build with Custom Port

```bash
poetry run mkdocs serve --dev-addr=127.0.0.1:8080
```

## Documentation Structure

```
docs/                           # User-facing documentation (GitHub Pages)
├── index.md                    # Home page
├── getting-started.md          # Installation & quickstart
├── configuration.md            # Configuration guide
├── profiles.md                 # Profiles documentation
├── imports.md                  # Imports guide
├── merge-order.md              # Merge semantics
├── security.md                 # Security & secrets
├── cli.md                      # Command-line interface
├── faq.md                      # FAQ
├── philosophy.md               # Design philosophy
├── roadmap.md                  # Future plans
└── api/                        # API Reference (auto-generated)
    ├── index.md                # API overview
    ├── core.md                 # Core API (load_config, Config, ConfigLoader)
    ├── secrets.md              # LazySecret API
    ├── utilities.md            # deep_merge, ConfigSingleton
    └── exceptions.md           # Error handling

sprig-config-module/docs/       # Developer guides (internal)
├── README_Developer_Guide.md   # Developer overview
├── release_checklist.md        # Release process
├── migration_guide.md          # Version migration guide
├── SprigConfig_ENC_BestPractices.md  # Secret best practices
├── GitLab.md                   # GitLab CI/CD
├── PyPI.md                     # PyPI publishing
└── ...
```

## Configuration

Documentation configuration is in `sprig-config-module/mkdocs.yml`:

```yaml
site_name: SprigConfig Documentation
theme:
  name: material
  palette:
    primary: green
    accent: light green

plugins:
  - search
  - mkdocstrings      # Auto-generate API docs from docstrings
  - git-revision-date-localized

nav:
  - Home: ../docs/index.md
  - Getting Started: ...
  - API Reference: ...
```

## API Reference Generation

API documentation is automatically generated from Python docstrings using mkdocstrings.

### How It Works

1. **Docstrings in source code:**
   ```python
   # src/sprigconfig/config.py
   class Config:
       """Dict-like configuration wrapper with dotted-key access.

       Args:
           data: Configuration data as nested dict
           meta: Optional metadata dict

       Example:
           >>> cfg = Config({"app": {"name": "MyApp"}})
           >>> cfg.get("app.name")
           'MyApp'
       """
   ```

2. **Reference in markdown:**
   ```markdown
   # docs/api/core.md
   ## Config

   ::: sprigconfig.Config
   ```

3. **Generated output:**
   MkDocs automatically extracts docstrings and generates formatted API documentation

### Supported Docstring Styles

SprigConfig uses **Google-style** docstrings:

```python
def load_config(profile: str, config_dir: Path = None) -> Config:
    """Load configuration with the specified profile.

    Args:
        profile: Profile name (e.g., 'dev', 'test', 'prod')
        config_dir: Optional config directory path

    Returns:
        Loaded configuration as Config object

    Raises:
        ConfigLoadError: If configuration cannot be loaded

    Example:
        >>> cfg = load_config(profile="dev")
        >>> cfg.get("app.name")
        'MyApp'
    """
```

## Previewing Changes

### Local Preview Workflow

1. Make changes to documentation files
2. Save the file
3. MkDocs auto-reloads in browser
4. Review changes
5. Iterate

### Testing Broken Links

```bash
# Build and check for broken links
poetry run mkdocs build --strict

# This will fail if there are:
# - Broken internal links
# - Missing navigation entries
# - Invalid markdown syntax
```

## Deploying Documentation

### GitHub Pages (Automated)

Documentation is automatically deployed to GitHub Pages on push to `main`:

```bash
# Manual deployment (if needed)
poetry run mkdocs gh-deploy
```

This will:
1. Build the documentation
2. Push to `gh-pages` branch
3. Trigger GitHub Pages deployment

### GitLab Pages

For GitLab Pages, add to `.gitlab-ci.yml`:

```yaml
pages:
  stage: deploy
  script:
    - cd sprig-config-module
    - poetry install --with docs
    - poetry run mkdocs build --site-dir ../public
  artifacts:
    paths:
      - public
  only:
    - main
```

## Customizing the Documentation

### Add a New Page

1. Create markdown file in `docs/`:
   ```bash
   touch docs/my-new-page.md
   ```

2. Add to navigation in `mkdocs.yml`:
   ```yaml
   nav:
     - My New Page: ../docs/my-new-page.md
   ```

3. Write content using markdown

### Add API Documentation

To document a new module:

1. Ensure module has docstrings:
   ```python
   # src/sprigconfig/my_module.py
   class MyClass:
       """My class description."""
       pass
   ```

2. Create API reference page:
   ```markdown
   # docs/api/my-module.md
   ## MyClass

   ::: sprigconfig.my_module.MyClass
   ```

3. Add to navigation:
   ```yaml
   nav:
     - API Reference:
         - My Module: ../docs/api/my-module.md
   ```

## Troubleshooting

### Issue: "No module named 'sprigconfig'"

**Solution:** Ensure you're running from `sprig-config-module/` directory where `src/` is located.

### Issue: Mkdocstrings can't find module

**Solution:** Check `paths` in mkdocs.yml:

```yaml
plugins:
  - mkdocstrings:
      handlers:
        python:
          paths: [src]  # Must point to source directory
```

### Issue: Live reload not working

**Solution:**
- Check firewall settings
- Try different port: `mkdocs serve --dev-addr=127.0.0.1:8080`
- Clear browser cache

### Issue: Broken links in navigation

**Solution:** Use relative paths from `mkdocs.yml` location:

```yaml
nav:
  - Home: ../docs/index.md           # Correct (relative to mkdocs.yml)
  - API: ../docs/api/core.md         # Correct
```

## Best Practices

1. **Write docstrings first** - Document code as you write it
2. **Use examples** - Include code examples in docstrings
3. **Test locally** - Always preview before committing
4. **Check links** - Run `mkdocs build --strict` before deploying
5. **Keep it organized** - Follow existing structure and patterns
6. **Update navigation** - Add new pages to `mkdocs.yml`

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)
- [Google-style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
