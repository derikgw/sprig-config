# 🌱 SprigConfig

SprigConfig is a Python configuration framework inspired by Spring Boot's flexible profile and deep-merge behavior — designed for modern Python apps that need clean, environment-specific configuration.

It supports:
- Profile-based configuration (`dev`, `test`, `prod`, etc.)
- Deep merge behavior with clear override rules
- Environment variable resolution (`${VAR:default}`)
- Secure encrypted secrets with `ENC()` format — now lazy-loaded

---

## 🚀 Getting Started

### Installation
```bash
pip install sprigconfig
```

---

## 📂 Project Structure
Example:
```
sprig-config-module/
│
├── config/
│   ├── application.yml
│   ├── application-dev.yml
│   ├── application-prod.yml
│   ├── application-test.yml
│   ├── features.yml
│   └── override.yml
│
├── docs/
│   └── security/
│       └── SprigConfig_ENC_BestPractices.md
│
└── src/
    └── sprigconfig/
```

---

## ⚙️ Usage Example
`application.yml`:
```yaml
server:
  port: 8080
app:
  profile: ${APP_PROFILE:dev}
logging:
  level: INFO
```

`application-dev.yml`:
```yaml
server:
  port: 9090
imports:
  - features.yml
```

Python:
```python
from sprigconfig import load_config

config = load_config()
print(config["server"]["port"])  # dev → 9090
```

---

## 🔐 Secrets Management (ENC)
SprigConfig supports encrypted values in YAML:
```yaml
username: ENC(gAAAAABokVDE6...)
password: ENC(gAAAAABokVDE3...)
```

Secrets are automatically detected wherever `ENC(...)` appears — no `secrets:` group or `encrypted: true` flag is required.

For detailed best practices:
📄 [Secrets Management & ENC() Best Practices](docs/security/SprigConfig_ENC_BestPractices.md)

---

## 🧪 Running Tests
```bash
pytest
pytest -m integration
```

---

## 🛣 Roadmap
- [x] Deep merge configuration loader
- [x] Profile-specific overrides
- [x] Environment variable resolution
- [x] ENC() secrets support
- [x] Lazy secret loading
- [ ] Key rotation for ENC values
- [ ] JSON & `.properties` config support

---

## 📜 License
This project is licensed under the MIT License.
