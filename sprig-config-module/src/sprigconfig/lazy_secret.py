# src/sprigconfig/lazy_secret.py
from typing import Optional

from cryptography.fernet import Fernet
from sprigconfig.exceptions import ConfigLoadError


class LazySecret:
    """
    Represents a value encrypted with ENC(...).
    Decrypts only when accessed via get() or __str__().
    """

    __slots__ = ("_encrypted_value", "_decrypted_value", "_key")

    def __init__(self, enc_value: str, key: Optional[str] = None):
        self._encrypted_value = enc_value[4:-1]
        self._decrypted_value = None
        self._key = key

    def _decrypt(self):
        if self._decrypted_value is not None:
            return self._decrypted_value
        if not self._key:
            raise ConfigLoadError("No key provided to LazySecret.")
        fernet = Fernet(self._key.encode() if isinstance(self._key, str) else self._key)
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
