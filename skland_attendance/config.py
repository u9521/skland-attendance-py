from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0


@dataclass(frozen=True)
class Config:
    tokens: list[str]
    max_retries: int = DEFAULT_MAX_RETRIES
    anonymous: bool = False
    timeout: float = DEFAULT_TIMEOUT


def split_comma(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None or value == "":
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    return True


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def build_config(args: argparse.Namespace) -> Config:
    tokens_value = args.tokens if args.tokens is not None else os.getenv("SKLAND_TOKENS")
    retries_value = args.max_retries
    timeout_value = args.timeout

    if retries_value is None:
        env_retries = os.getenv("SKLAND_MAX_RETRIES")
        retries_value = int(env_retries) if env_retries else DEFAULT_MAX_RETRIES

    if timeout_value is None:
        env_timeout = os.getenv("SKLAND_TIMEOUT")
        timeout_value = float(env_timeout) if env_timeout else DEFAULT_TIMEOUT

    if args.anonymous is None:
        anonymous = parse_bool(os.getenv("SKLAND_ANONYMOUS"), default=False)
    else:
        anonymous = args.anonymous

    return Config(
        tokens=split_comma(tokens_value),
        max_retries=retries_value,
        anonymous=anonymous,
        timeout=timeout_value,
    )
