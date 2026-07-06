from __future__ import annotations

import argparse
import sys

from .config import build_config, positive_float, positive_int
from .attendance.runner import run_attendance


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="森空岛每日签到")
    parser.add_argument(
        "--tokens",
        help="覆盖 SKLAND_TOKENS，多个账号用英文逗号分隔",
    )
    parser.add_argument(
        "--max-retries",
        type=positive_int,
        help="覆盖 SKLAND_MAX_RETRIES，单角色失败后的最大重试次数",
    )
    parser.add_argument(
        "--anonymous",
        action="store_true",
        dest="anonymous",
        default=None,
        help="开启匿名输出，覆盖 SKLAND_ANONYMOUS",
    )
    parser.add_argument(
        "--no-anonymous",
        action="store_false",
        dest="anonymous",
        help="关闭匿名输出，覆盖 SKLAND_ANONYMOUS",
    )
    parser.add_argument(
        "--timeout",
        type=positive_float,
        help="覆盖 SKLAND_TIMEOUT，单位秒",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = build_config(args)
    except ValueError as exc:
        parser.error(str(exc))

    if not config.tokens:
        parser.print_help()
        raise SystemExit(1)

    raise SystemExit(run_attendance(config))


if __name__ == "__main__":
    main(sys.argv[1:])
