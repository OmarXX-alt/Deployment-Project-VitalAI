from __future__ import annotations

from marshmallow import Schema, ValidationError, fields, validates_schema
from marshmallow.validate import Length, OneOf, Range


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


class ProfileUpdateSchema(Schema):
    display_name = fields.Str(required=False, validate=Length(min=2, max=50))
    daily_calorie_target = fields.Int(required=False, validate=Range(min=500, max=10000))
    hydration_goal = fields.Int(required=False, validate=Range(min=250, max=10000))
    wellness_goal = fields.Str(required=False, validate=Length(max=200))


class WorkoutLogSchema(Schema):
    exercise_type = fields.Str(required=True, validate=Length(min=1, max=100))
    duration_minutes = fields.Int(required=True, validate=Range(min=1, max=600))
    sets = fields.Int(required=False, validate=Range(min=1))
    reps = fields.Int(required=False, validate=Range(min=1))
    intensity = fields.Str(required=True, validate=OneOf(["low", "moderate", "high"]))
    logged_at = fields.DateTime(required=False, format="iso")


class MealLogSchema(Schema):
    meal_name = fields.Str(required=True, validate=Length(min=1, max=100))
    calories = fields.Int(required=True, validate=Range(min=0, max=5000))
    meal_type = fields.Str(
        required=True,
        validate=OneOf(["breakfast", "lunch", "dinner", "snack"]),
    )
    logged_at = fields.DateTime(required=False, format="iso")


class SleepLogSchema(Schema):
    sleep_start = fields.DateTime(required=True, format="iso")
    sleep_end = fields.DateTime(required=True, format="iso")
    quality_score = fields.Int(required=True, validate=Range(min=1, max=5))

    @validates_schema
    def validate_sleep_times(self, data, **kwargs):
        start = data.get("sleep_start")
        end = data.get("sleep_end")
        if start and end and end <= start:
            raise ValidationError("sleep_end must be after sleep_start.")


class HydrationLogSchema(Schema):
    amount_ml = fields.Int(required=True, validate=Range(min=50, max=5000))
    logged_at = fields.DateTime(required=False, format="iso")


class MoodLogSchema(Schema):
    mood_score = fields.Int(required=True, validate=Range(min=1, max=5))
    note = fields.Str(required=False, validate=Length(max=500))
