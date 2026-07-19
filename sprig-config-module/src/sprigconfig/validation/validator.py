from dataclasses import MISSING, fields, is_dataclass
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from ..exceptions import ConfigValidationError


def validate_schema(config: dict[str, Any], schema: type) -> None:
    if not isinstance(config, dict):
        raise ConfigValidationError("Schema validation requires a mapping configuration root.")
    if not is_dataclass(schema):
        raise ConfigValidationError(
            "Schema must be a dataclass type for validation."
        )
    _validate_dataclass(config, schema, path="")


def _validate_dataclass(value: dict[str, Any], schema_type: type, *, path: str) -> None:
    if not isinstance(value, dict):
        location = path or "<root>"
        raise ConfigValidationError(
            f"Type mismatch at '{location}': expected mapping for {schema_type.__name__}, got {type(value).__name__}."
        )

    schema_fields = fields(schema_type)
    type_hints = get_type_hints(schema_type)

    expected_keys = {f.name for f in schema_fields}
    for key in value.keys():
        if key not in expected_keys:
            dotted = _join_path(path, key)
            raise ConfigValidationError(f"Unknown key '{dotted}'.")

    for field in schema_fields:
        dotted = _join_path(path, field.name)
        required = field.default is MISSING and field.default_factory is MISSING

        if field.name not in value:
            if required:
                raise ConfigValidationError(f"Missing required key '{dotted}'.")
            continue

        expected_type = type_hints.get(field.name, Any)
        _validate_value(value[field.name], expected_type, path=dotted)


def _validate_value(value: Any, expected_type: Any, *, path: str) -> None:
    if expected_type is Any:
        return

    origin = get_origin(expected_type)
    args = get_args(expected_type)

    if origin in (Union, UnionType):
        for candidate in args:
            try:
                _validate_value(value, candidate, path=path)
                return
            except ConfigValidationError:
                continue
        _raise_type_mismatch(path, expected_type, value)

    if is_dataclass(expected_type):
        _validate_dataclass(value, expected_type, path=path)
        return

    if origin in (list,):
        if not isinstance(value, list):
            _raise_type_mismatch(path, expected_type, value)
        item_type = args[0] if args else Any
        for idx, item in enumerate(value):
            _validate_value(item, item_type, path=f"{path}[{idx}]")
        return

    if origin in (dict,):
        if not isinstance(value, dict):
            _raise_type_mismatch(path, expected_type, value)
        key_type = args[0] if len(args) > 0 else Any
        val_type = args[1] if len(args) > 1 else Any
        for key, item in value.items():
            _validate_value(key, key_type, path=f"{path}.<key>")
            _validate_value(item, val_type, path=_join_path(path, str(key)))
        return

    if isinstance(expected_type, type):
        if expected_type is bool:
            if not isinstance(value, bool):
                _raise_type_mismatch(path, expected_type, value)
            return
        if expected_type is int:
            if not isinstance(value, int) or isinstance(value, bool):
                _raise_type_mismatch(path, expected_type, value)
            return
        if not isinstance(value, expected_type):
            _raise_type_mismatch(path, expected_type, value)
        return

    # If typing construct is unsupported, do not silently accept unknown structures.
    _raise_type_mismatch(path, expected_type, value)


def _raise_type_mismatch(path: str, expected_type: Any, value: Any) -> None:
    raise ConfigValidationError(
        f"Type mismatch at '{path}': expected {_type_name(expected_type)}, got {type(value).__name__}."
    )


def _type_name(expected_type: Any) -> str:
    origin = get_origin(expected_type)
    if origin is None:
        return getattr(expected_type, "__name__", str(expected_type))
    args = ", ".join(_type_name(arg) for arg in get_args(expected_type))
    return f"{origin.__name__}[{args}]"


def _join_path(path: str, key: str) -> str:
    if not path:
        return key
    return f"{path}.{key}"
