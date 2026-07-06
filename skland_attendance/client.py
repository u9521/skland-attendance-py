from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Any
from urllib.parse import urlencode

import requests

from .models import JsonDict


SKLAND_APP_CODE = "4ca99fa6b56cc2ba"
SERVER_TIMESTAMP_OFFSET = 2
BASE_URL = "https://zonai.skland.com"
HYPERGRYPH_BASE_URL = "https://as.hypergryph.com"
APP_USER_AGENT = "Mozilla/5.0 (Linux; Android 12; SM-A5560 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.61 Safari/537.36; SKLand/1.52.1"
WEB_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def json_dumps(value: JsonDict) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


class SklandError(RuntimeError):
    pass


class SklandClient:
    def __init__(self, *, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.did = f"B{uuid.uuid4().hex}"
        self.token: str | None = None
        self.cred: str | None = None
        self.user_id: str | None = None

    def grant_authorize_code(self, token: str) -> str:
        res = self._hypergryph_request(
            "POST",
            "/user/oauth2/v2/grant",
            json_body={"appCode": SKLAND_APP_CODE, "token": self._parse_oauth_token(token), "type": 0},
            error_message="通过 OAuth 登录凭证验证鹰角网络通行证错误",
        )
        code = res.get("code")
        if not code:
            raise SklandError("授权响应中缺少 code")
        return str(code)

    def sign_in(self, authorize_code: str) -> None:
        res = self.session.post(
            f"{BASE_URL}/web/v1/user/auth/generate_cred_by_code",
            headers={
                "content-type": "application/json",
                "user-agent": WEB_USER_AGENT,
                "referer": "https://www.skland.com/",
                "origin": "https://www.skland.com",
                "dId": self.did,
                "platform": "3",
                "timestamp": str(int(time.time())),
                "vName": "1.0.0",
            },
            json={"code": authorize_code, "kind": 1},
            timeout=self.timeout,
        )
        data = self._json_response(res, "生成森空岛 cred 错误").get("data") or {}
        self.token = data.get("token")
        self.cred = data.get("cred")
        self.user_id = data.get("userId")
        if not self.token or not self.cred:
            raise SklandError("登录响应中缺少 token 或 cred")

    def get_binding(self) -> JsonDict:
        return self._skland_request("GET", "/api/v1/game/player/binding", error_message="获取游戏绑定信息错误")

    def get_arknights_attendance_status(self, *, uid: str, game_id: int) -> JsonDict:
        return self._skland_request(
            "GET",
            "/api/v1/game/attendance",
            query={"uid": uid, "gameId": game_id},
            error_message="获取签到状态错误",
        )

    def arknights_attendance(self, *, uid: str, game_id: int) -> JsonDict:
        return self._skland_request(
            "POST",
            "/api/v1/game/attendance",
            json_body={"uid": uid, "gameId": game_id},
            error_message="执行签到错误",
        )

    def get_endfield_attendance_status(self, *, game_id: int, role_id: str, server_id: str) -> JsonDict:
        return self._skland_request(
            "GET",
            "/api/v1/game/endfield/attendance",
            headers={"content-type": "application/json", "sk-game-role": f"{game_id}_{role_id}_{server_id}"},
            error_message="获取签到状态错误",
        )

    def endfield_attendance(self, *, game_id: int, role_id: str, server_id: str) -> JsonDict:
        return self._skland_request(
            "POST",
            "/api/v1/game/endfield/attendance",
            headers={
                "content-type": "application/json",
                "sk-game-role": f"{game_id}_{role_id}_{server_id}",
                "referer": "https://game.skland.com/",
                "origin": "https://game.skland.com/",
            },
            error_message="获取签到信息错误",
        )

    def _hypergryph_request(self, method: str, path: str, *, json_body: JsonDict, error_message: str) -> JsonDict:
        res = self.session.request(
            method,
            f"{HYPERGRYPH_BASE_URL}{path}",
            headers={
                "user-agent": APP_USER_AGENT,
                "dId": self.did,
                "x-requested-with": "com.hypergryph.skland",
                "content-type": "application/json",
            },
            json=json_body,
            timeout=self.timeout,
        )
        data = self._json_response(res, error_message)
        if data.get("status") != 0 or data.get("msg") != "OK" or "data" not in data:
            raise SklandError(f"{error_message}: {data.get('msg') or data}")
        return data["data"]

    def _skland_request(
        self,
        method: str,
        path: str,
        *,
        query: JsonDict | None = None,
        json_body: JsonDict | None = None,
        headers: dict[str, str] | None = None,
        error_message: str,
    ) -> JsonDict:
        if not self.token or not self.cred:
            raise SklandError("森空岛 token 或 cred 未设置")

        body = json_dumps(json_body) if json_body else None
        request_headers = self._signed_headers(path, query=query, body=body, headers=headers)
        if body and not any(key.lower() == "content-type" for key in request_headers):
            request_headers["content-type"] = "application/json"
        res = self.session.request(
            method,
            f"{BASE_URL}{path}",
            params=query,
            data=body,
            headers=request_headers,
            timeout=self.timeout,
        )
        data = self._json_response(res, error_message)
        if data.get("code") != 0:
            raise SklandError(f"{error_message}: {data.get('message') or data}")
        return data.get("data") or {}

    def _signed_headers(
        self,
        path: str,
        *,
        query: JsonDict | None,
        body: str | None,
        headers: dict[str, str] | None,
    ) -> dict[str, str]:
        timestamp = str(int(time.time()) - SERVER_TIMESTAMP_OFFSET)
        signature_headers = {
            "platform": "3",
            "timestamp": timestamp,
            "dId": self.did,
            "vName": "1.0.0",
        }
        query_string = urlencode(query or {})
        payload = f"{path}{query_string}{body or ''}{timestamp}{json_dumps(signature_headers)}"
        signature = hashlib.md5(hmac.new(self.token.encode(), payload.encode(), hashlib.sha256).hexdigest().encode()).hexdigest()

        signed_headers = {
            "user-agent": APP_USER_AGENT,
            "accept-encoding": "gzip",
            "connection": "close",
            "x-requested-with": "com.hypergryph.skland",
            "cred": self.cred,
            "sign": signature,
            **signature_headers,
        }
        if headers:
            signed_headers.update(headers)
        return signed_headers

    @staticmethod
    def _parse_oauth_token(token: str) -> str:
        try:
            parsed: Any = json.loads(token)
        except json.JSONDecodeError:
            return token
        content = parsed.get("data", {}).get("content") if isinstance(parsed, dict) else None
        return str(content) if content else token

    @staticmethod
    def _json_response(res: requests.Response, error_message: str) -> JsonDict:
        try:
            data = res.json()
        except ValueError as exc:
            raise SklandError(f"{error_message}: HTTP {res.status_code}, 响应不是 JSON") from exc
        if not res.ok:
            raise SklandError(f"{error_message}: HTTP {res.status_code}, {data}")
        return data
