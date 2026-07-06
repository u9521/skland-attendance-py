from __future__ import annotations

from .models import JsonDict


def mask_nickname(name: str) -> str:
    if len(name) <= 1:
        return "*"
    return f"{name[0]}{'*' * (len(name) - 1)}"


def format_character_name(character: JsonDict, app_name: str | None = None, *, anonymous: bool = False) -> str:
    game_prefix = f"[{app_name}]" if app_name else ""
    channel_name = character.get("channelName", "")
    return f"{game_prefix}{channel_name}角色 {format_privacy_name(character, anonymous=anonymous)}"


def format_privacy_name(character: JsonDict, *, anonymous: bool = False) -> str:
    if character.get("gameId") == 3:
        role = character.get("defaultRole") or {}
        nickname = "管理员" if anonymous else mask_nickname(str(role.get("nickname") or ""))
        return f"{nickname} lv.{role.get('level') or 0}"

    nick_name = str(character.get("nickName") or "")
    name, sep, number = nick_name.partition("#")
    if not name or not sep:
        raise ValueError("Unexpected Error: 明日方舟 nickName 格式不正确")

    display_name = "博士 " if anonymous else mask_nickname(name)
    return f"{display_name}#{number}"


def format_arknights_awards(awards: list[JsonDict]) -> str:
    return ",".join(f"「{award.get('resource', {}).get('name', '未知奖励')}」{award.get('count', 1)}个" for award in awards)


def format_endfield_awards(award_ids: list[JsonDict], resource_info_map: dict[str, JsonDict]) -> str:
    formatted = []
    for award_id in award_ids:
        key = str(award_id.get("id"))
        award = resource_info_map.get(key)
        if not award:
            formatted.append("「未知奖励」1个")
        else:
            formatted.append(f"「{award.get('name', '未知奖励')}」{award.get('count', 1)}个")
    return ",".join(formatted)
