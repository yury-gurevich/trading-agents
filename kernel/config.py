"""Environment-driven configuration and the justified-tunable primitive.

Agent: kernel
Role: isolate every configurable value into one env-overridable place, and force
      each processing/forecast constant to record why its default was chosen.
External I/O: process environment and the .env file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo


def tunable(
    default: Any,  # noqa: ANN401 - a tunable's default may be of any type
    *,
    why: str,
    ge: float | None = None,
    gt: float | None = None,
    le: float | None = None,
    unit: str | None = None,
    validation_alias: AliasChoices | str | None = None,
) -> Any:  # noqa: ANN401 - returns a pydantic FieldInfo, assigned to a typed field
    """Declare a configurable constant.

    ``why`` — the justification for this default — is mandatory: no tunable may be
    introduced without recording why its value was chosen. ``ge``/``gt``/``le`` bound
    it so an operator override cannot push it outside a safe range. Every constant
    that influences processing or a forecast must be declared through this helper
    rather than written as a bare literal.
    """
    extra: dict[str, Any] | None = {"unit": unit} if unit is not None else None
    return Field(
        default,
        description=why,
        ge=ge,
        gt=gt,
        le=le,
        json_schema_extra=extra,
        validation_alias=validation_alias,
    )


class AgentSettings(BaseSettings):
    """Base for every agent's settings: reads ``.env`` then the process environment.

    Subclasses set ``env_prefix`` so each agent's variables are namespaced, and the
    model is frozen so configuration cannot drift mid-run.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )


class TunableDoc(BaseModel):
    """One row of the constants catalogue — what the dashboard and docs render."""

    model_config = ConfigDict(frozen=True)

    name: str
    env_var: str
    default: Any
    justification: str
    minimum: float | None = None
    maximum: float | None = None
    unit: str | None = None


def _limit(info: FieldInfo, attr: str) -> float | None:
    """Pull a numeric bound (ge/le) off a field's annotated-type metadata."""
    for meta in info.metadata:
        value = getattr(meta, attr, None)
        if value is not None:
            return float(value)
    return None


def _lower_limit(info: FieldInfo) -> float | None:
    """Pull either inclusive or exclusive lower bound metadata."""
    inclusive = _limit(info, "ge")
    return inclusive if inclusive is not None else _limit(info, "gt")


def describe(settings_cls: type[AgentSettings]) -> list[TunableDoc]:
    """Introspect a settings class into its tunable catalogue.

    This is what gives central visibility: every justified constant in the system
    can be listed — with its env var, default, justification, and bounds — without
    reading the source.
    """
    prefix = str(settings_cls.model_config.get("env_prefix", ""))
    catalogue: list[TunableDoc] = []
    for name, info in settings_cls.model_fields.items():
        extra = (
            info.json_schema_extra if isinstance(info.json_schema_extra, dict) else {}
        )
        unit = extra.get("unit")
        catalogue.append(
            TunableDoc(
                name=name,
                env_var=f"{prefix}{name}".upper(),
                default=info.get_default(),
                justification=info.description or "",
                minimum=_lower_limit(info),
                maximum=_limit(info, "le"),
                unit=str(unit) if unit is not None else None,
            )
        )
    return catalogue
