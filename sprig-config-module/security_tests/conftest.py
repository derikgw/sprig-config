"""Security tests deliberately do not load .env files or production fixtures."""
import os

from hypothesis import settings


settings.register_profile("security", max_examples=50, deadline=None, derandomize=True)
settings.register_profile("security-deep", max_examples=500, deadline=None)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "security"))
