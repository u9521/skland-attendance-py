from __future__ import annotations

from datetime import datetime, timezone, timedelta

from ..client import SklandClient
from ..formatters import format_arknights_awards, format_character_name, format_endfield_awards
from ..models import AttendanceResult, JsonDict


SHANGHAI_TZ = timezone(timedelta(hours=8))


def is_today_attended(attendance_status: JsonDict) -> bool:
    if "records" in attendance_status:
        today = datetime.now(SHANGHAI_TZ).date()
        for record in attendance_status.get("records") or []:
            ts = record.get("ts")
            if ts is None:
                continue
            record_date = datetime.fromtimestamp(int(ts), SHANGHAI_TZ).date()
            if record_date == today:
                return True
        return False

    return bool(attendance_status.get("hasToday"))


def attend_character(client: SklandClient, character: JsonDict, *, app_name: str, anonymous: bool) -> AttendanceResult:
    character_label = format_character_name(character, app_name, anonymous=anonymous)
    game_id = int(character.get("gameId") or 0)

    if game_id == 1:
        return attend_arknights(client, character, character_label)
    if game_id == 3:
        return attend_endfield(client, character, character_label)

    return AttendanceResult(False, f"{character_label} 不支持的游戏 (gameId: {game_id})", True)


def attend_arknights(client: SklandClient, character: JsonDict, character_label: str) -> AttendanceResult:
    query = {"uid": str(character.get("uid")), "game_id": int(character.get("gameId"))}
    status = client.get_arknights_attendance_status(uid=query["uid"], game_id=query["game_id"])
    if is_today_attended(status):
        return AttendanceResult(False, f"{character_label} 今天已经签到过了", False)

    data = client.arknights_attendance(uid=query["uid"], game_id=query["game_id"])
    awards = format_arknights_awards(data.get("awards") or [])
    return AttendanceResult(True, f"{character_label} 签到成功，获得了{awards}", False)


def attend_endfield(client: SklandClient, character: JsonDict, character_label: str) -> AttendanceResult:
    role = character.get("defaultRole")
    if not role:
        return AttendanceResult(False, f"{character_label} 没有角色，跳过签到", False)

    game_id = int(character.get("gameId"))
    role_id = str(role.get("roleId"))
    server_id = str(role.get("serverId"))
    status = client.get_endfield_attendance_status(game_id=game_id, role_id=role_id, server_id=server_id)
    if is_today_attended(status):
        return AttendanceResult(False, f"{character_label} 今天已经签到过了", False)

    data = client.endfield_attendance(game_id=game_id, role_id=role_id, server_id=server_id)
    awards = format_endfield_awards(data.get("awardIds") or [], data.get("resourceInfoMap") or {})
    return AttendanceResult(True, f"{character_label} 签到成功，获得了{awards}", False)
