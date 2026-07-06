from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


JsonDict = dict[str, Any]


@dataclass
class AttendanceResult:
    success: bool
    message: str
    has_error: bool = False


@dataclass
class GameStats:
    game_name: str
    total: int = 0
    succeeded: int = 0
    already_attended: int = 0
    failed: int = 0


@dataclass
class AccountStats:
    total: int
    successful: int = 0
    failed: int = 0
    failed_indexes: list[int] = field(default_factory=list)


@dataclass
class ExecutionStats:
    accounts: AccountStats
    characters_by_game: dict[int, GameStats] = field(default_factory=dict)
