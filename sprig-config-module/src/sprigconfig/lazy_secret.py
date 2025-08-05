# src/sprigconfig/lazy_secret.py
import os
from cryptography.fernet import Fernet
from sprigconfig.exceptions import ConfigLoadError


class LazySecret:
    """
    Represents a value encrypted with ENC(...).
    Decrypts only when accessed via get() or __str__().
    """

    __slots__ = ("_encrypted_value", "_decrypted_value")

    def __init__(self, enc_value: str):
        if not (enc_value.startswith("ENC(") and enc_value.endswith(")")):
            raise ValueError("LazySecret must wrap ENC(...) value")

        self._encrypted_value = enc_value[4:-1]  # strip ENC(...)
        self._decrypted_value = None  # decrypted only on demand

    def _decrypt(self):
        if self._decrypted_value is not None:
            return self._decrypted_value

        key = os.getenv("APP_SECRET_KEY")
        if not key:
            raise ConfigLoadError("APP_SECRET_KEY is required to decrypt secrets")

        fernet = Fernet(key.encode() if isinstance(key, str) else key)
        self._decrypted_value = fernet.decrypt(self._encrypted_value.encode()).decode()
        return self._decrypted_value

    def get(self) -> str:
        """
        Returns the decrypted value. Caller responsible for zeroizing if needed.
        """
        return self._decrypt()

    def __str__(self):
        """If cast to string, return the decrypted value (use with care)."""
        return self._decrypt()

    def zeroize(self):
        """
        Overwrite decrypted value in memory (best effort).
        """
        if self._decrypted_value is not None:
            # Overwrite string contents by replacing with same-length zeros
            self._decrypted_value = "\0" * len(self._decrypted_value)
            self._decrypted_value = None
