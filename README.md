# 森空岛签到 Python 版

面向 CI 环境的森空岛每日签到程序。

## 特性

- 使用 `uv` 运行，启动快，运行时仅依赖 `requests`
- 支持多个森空岛账号，使用英文逗号分隔 token
- 支持明日方舟和明日方舟：终末地签到
- 支持命令行参数覆盖环境变量配置

## 配置

| 名称 | 来源 | 说明 |
| --- | --- | --- |
| `SKLAND_TOKENS` | Repository secrets | 必填，森空岛凭据，多个账号用英文逗号分隔 |
| `SKLAND_MAX_RETRIES` | Repository variables | 可选，最大重试次数，默认 `3` |
| `SKLAND_ANONYMOUS` | Repository variables | 可选，隐藏角色名，`true` / `1` / `yes` 等表示开启，默认关闭 |
| `SKLAND_TIMEOUT` | Environment variables | 可选，请求超时时间，单位秒，默认 `30` |

配置优先级：命令行参数 > 环境变量 > 默认值。

## 本地运行

```bash
uv sync
SKLAND_TOKENS="your-token" uv run skland-attendance
```

命令行覆盖环境变量：

```bash
uv run skland-attendance --tokens "your-token" --max-retries 5 --anonymous
uv run skland-attendance --tokens "your-token" --no-anonymous
```

也可以使用模块入口：

```bash
uv run python -m skland_attendance --tokens "your-token"
```

## GitHub Actions

项目内置 `.github/workflows/attendance.yml`，默认每天 UTC 15:00 运行，也支持手动触发。

需要在仓库中配置：

- Repository secret: `SKLAND_TOKENS`
- Repository variable: `SKLAND_MAX_RETRIES`
- Repository variable: `SKLAND_ANONYMOUS`

`SKLAND_TOKENS` 获取方式：登录森空岛或鹰角网络通行证后，打开账号信息接口并复制返回 JSON 中的 `content` 字段。

登录 [森空岛网页版](https://www.skland.com/) 后，打开 https://web-api.skland.com/account/info/hg

或者登录 [鹰角网络通行证](https://user.hypergryph.com/login) 后，打开 https://web-api.hypergryph.com/account/info/hg

## 退出码

- `0`：全部角色签到成功或今天已签到
- `1`：缺少 `SKLAND_TOKENS`，或至少一个账号/角色最终失败

## 致谢

感谢上游项目 [AEtherside/skland-daily-attendance](https://github.com/AEtherside/skland-daily-attendance)。本项目的签到流程和 CI 方案参考了该项目，并在 Python 版本中移除了持久化存储、Docker 和消息通知功能。
