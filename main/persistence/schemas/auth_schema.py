from __future__ import annotations

from marshmallow import Schema, ValidationError, fields, pre_load, validates
from marshmallow.validate import Length


def validate_schema(schema: Schema, data: dict) -> tuple[dict, list[str]]:
    try:
        return schema.load(data), []
    except ValidationError as exc:
        return {}, _flatten_errors(exc.messages)


def _flatten_errors(errors, prefix: str = "") -> list[str]:
    flattened: list[str] = []
    if isinstance(errors, dict):
        for key, value in errors.items():
            key_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.extend(_flatten_errors(value, key_prefix))
    elif isinstance(errors, list):
        for item in errors:
            if isinstance(item, (dict, list)):
                flattened.extend(_flatten_errors(item, prefix))
            else:
                flattened.append(f"{prefix}: {item}" if prefix else str(item))
    else:
        flattened.append(f"{prefix}: {errors}" if prefix else str(errors))
    return flattened


class RegisterSchema(Schema):
    display_name = fields.Str(required=True, validate=Length(min=2, max=50))
    email = fields.Email(required=True)
    password = fields.Str(
        required=True, validate=Length(min=8), load_only=True
    )

    @pre_load
    def normalize_email(self, data, **kwargs):
        email = data.get("email")
        if isinstance(email, str):
            data["email"] = email.strip().lower()
        return data

    @validates("email")
    def validate_email(self, value):
        normalized = value.strip().lower()
        if value != normalized:
            raise ValidationError("Email must be lowercase and trimmed.")


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)

    @pre_load
    def normalize_email(self, data, **kwargs):
        email = data.get("email")
        if isinstance(email, str):
            data["email"] = email.strip().lower()
        return data

    @validates("email")
    def validate_email(self, value):
        normalized = value.strip().lower()
        if value != normalized:
            raise ValidationError("Email must be lowercase and trimmed.")
