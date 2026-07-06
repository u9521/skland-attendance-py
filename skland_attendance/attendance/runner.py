from __future__ import annotations

from ..client import SklandClient
from ..config import Config
from ..models import AccountStats, ExecutionStats, GameStats, JsonDict
from ..retry import retry
from .handlers import attend_character


SUPPORTED_APP_CODES = {"arknights", "endfield"}


def run_attendance(config: Config) -> int:
    if not config.tokens:
        print("未配置 SKLAND_TOKENS，无法执行签到")
        return 1

    print("森空岛每日签到")
    stats = ExecutionStats(accounts=AccountStats(total=len(config.tokens)))

    for index, token in enumerate(config.tokens, start=1):
        print(f"\n--- 账号 {index}/{len(config.tokens)} ---")
        try:
            account_has_error = process_account(token, index, config, stats)
        except Exception as exc:
            print(f"处理失败: {exc}")
            stats.accounts.failed += 1
            stats.accounts.failed_indexes.append(index)
            continue

        if account_has_error:
            stats.accounts.failed += 1
            stats.accounts.failed_indexes.append(index)
        else:
            stats.accounts.successful += 1

    print_summary(stats)
    return 1 if stats.accounts.failed else 0


def process_account(token: str, account_number: int, config: Config, stats: ExecutionStats) -> bool:
    print("开始处理...")
    client = SklandClient(timeout=config.timeout)
    code = client.grant_authorize_code(token)
    client.sign_in(code)

    binding = client.get_binding()
    characters = expand_characters(binding)
    if not characters:
        print("未找到支持签到的角色")
        return False

    account_has_error = False
    for character, app_name in characters:
        game_id = int(character.get("gameId") or 0)
        game_stats = stats.characters_by_game.setdefault(game_id, GameStats(game_name=str(character.get("gameName") or app_name)))
        game_stats.total += 1

        try:
            result = retry(
                lambda c=character, name=app_name: attend_character(client, c, app_name=name, anonymous=config.anonymous),
                retries=config.max_retries,
                on_retry=lambda retries_left, exc: print(f"操作失败，剩余重试次数: {retries_left}: {exc}"),
            )
        except Exception as exc:
            print(f"签到过程中出现未知错误: {exc}")
            game_stats.failed += 1
            account_has_error = True
            continue

        print(result.message)
        if result.has_error:
            game_stats.failed += 1
            account_has_error = True
        elif result.success:
            game_stats.succeeded += 1
        else:
            game_stats.already_attended += 1

    return account_has_error


def expand_characters(binding: JsonDict) -> list[tuple[JsonDict, str]]:
    characters: list[tuple[JsonDict, str]] = []
    for app_binding in binding.get("list") or []:
        app_code = app_binding.get("appCode")
        if app_code not in SUPPORTED_APP_CODES:
            continue

        app_name = str(app_binding.get("appName") or app_binding.get("gameName") or app_code)
        for player in app_binding.get("bindingList") or []:
            if app_code == "endfield":
                roles = player.get("roles") or []
                if roles:
                    for role in roles:
                        expanded = dict(player)
                        expanded["defaultRole"] = role
                        expanded["roles"] = [role]
                        characters.append((expanded, app_name))
                else:
                    characters.append((player, app_name))
            else:
                characters.append((player, app_name))
    return characters


def print_summary(stats: ExecutionStats) -> None:
    print("\n========== 执行摘要 ==========")
    print("账号统计:")
    print(f"  • 总数: {stats.accounts.total}")
    print(f"  • 成功: {stats.accounts.successful}")
    if stats.accounts.failed:
        failed = ", #".join(str(i) for i in stats.accounts.failed_indexes)
        print(f"  • 失败: {stats.accounts.failed} (账号 #{failed})")

    for game_stats in stats.characters_by_game.values():
        print(f"\n【{game_stats.game_name}】角色统计:")
        print(f"  • 总数: {game_stats.total}")
        print(f"  • 本次签到成功: {game_stats.succeeded}")
        print(f"  • 今天已签到: {game_stats.already_attended}")
        if game_stats.failed:
            print(f"  • 签到失败: {game_stats.failed}")
