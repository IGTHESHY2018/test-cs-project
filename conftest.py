"""pytest 全局配置：鉴权 fixture + client 注入 + allure 环境信息。

F1 身份与访问控制需要的 fixture：
  - admin_token : 管理员 token（POST /users/login，session 级，整个测试跑一次）
  - user_token  : 用户 token（POST /yonghu/login，session 级，整个测试跑一次）
  - client      : 注入指定 token 后的 ApiClient（function 级，每个用例拿干净的 client）

Token 获取策略：
  按 yaml 里的 auth 字段选 fixture：
    auth=none  → 不调 token fixture，直接调 @IgnoreAuth 接口
    auth=user  → 用 user_token fixture 注入 token
    auth=admin → 用 admin_token fixture 注入 token
"""
from __future__ import annotations

import allure
import pytest

from apis import UsersApi, YonghuApi
from common import client
from config import get_config


# ============================================================
# Session 级 token fixture（整个测试会话只登录一次）
# ============================================================

@pytest.fixture(scope="session")
def admin_token() -> str | None:
    """管理员 token。用 config 里的 admin 账号调 /users/login 获取。

    返回 token 字符串；登录失败返回 None（用例自行判定 skip）。
    整个 session 只登录一次，后续用例复用同一个 token。
    """
    cfg = get_config()
    acct = cfg["account"]["admin"]
    username = acct["username"]
    password = acct["password"]

    # TODO 你写：
    #   1. 调 UsersApi().login(username, password) 拿响应 dict
    #   2. 从响应里取 token：字段名是 cfg["account"]["token_field"]
    #      （token_field 在 config.yaml 里写的是 "token"，所以响应里 resp["token"] 就是）
    #   3. 可选：allure.attach(token[:12]+"...", "admin_token", allure.attachment_type.TEXT)
    #      在报告里留个痕迹方便排障
    #   4. return token
    resp = UsersApi().login(username, password)
    return resp.get(cfg["account"]["token_field"])


@pytest.fixture(scope="session")
def user_token() -> str | None:
    """用户 token。用 config 里的 user 账号调 /yonghu/login 获取。

    返回 token 字符串；登录失败返回 None。
    整个 session 只登录一次。
    """
    cfg = get_config()
    acct = cfg["account"]["user"]
    username = acct["username"]
    password = acct["password"]

    # TODO 你写：和 admin_token 同理，只是换成 YonghuApi().login(...)
    #   resp = YonghuApi().login(username, password)
    #   token = resp.get(cfg["account"]["token_field"])
    #   return token
    resp=YonghuApi().login(username, password)
    return resp.get(cfg["account"]["token_field"])


# ============================================================
# Function 级 fixture
# ============================================================

@pytest.fixture(scope="function", autouse=True)
def auth_client(request):
    """按 pytest marker @pytest.mark.auth('admin'|'user'|'none') 注入对应 token。

    用法示例：
        @pytest.mark.auth('admin')
        def test_something(auth_client):
            api = YonghuApi()
            api.session()  # 请求自动带 admin token

    如果用例没打 auth marker，默认不带 token（等同于 auth='none'）。
    """
    marker = request.node.get_closest_marker("auth")
    role = marker.args[0] if marker and marker.args else "none"

    # TODO 你写：
    #   1. 按 role 取 token：
    #        admin → request.getfixturevalue("admin_token")
    #        user  → request.getfixturevalue("user_token")
    #        none  → None
    #   2. client.set_token(token)   # 注入到全局单例 client
    #   3. yield                       # 此时用例执行，请求自动带 Token header
    #   4. client.set_token(None)     # teardown 清 token，防用例间泄漏
    if role == "admin":
        token = request.getfixturevalue("admin_token")
    elif role == "user":
        token = request.getfixturevalue("user_token")
    else:
        token = None

    client.set_token(token)
    yield
    client.set_token(None)


# ============================================================
# allure 环境信息（报告里显示当前跑的是哪个环境）
# ============================================================

def pytest_sessionstart(session):
    """测试开始时把环境信息写入 allure 报告。"""
    cfg = get_config()
    env_name = cfg.get("_env", "unknown")
    allure_dir = session.config.getoption("--alluredir", default=None)
    if allure_dir:
        from pathlib import Path
        env_file = Path(allure_dir) / "environment.properties"
        env_file.parent.mkdir(parents=True, exist_ok=True)
        props = {
            "Environment": env_name,
            "BaseURL": cfg["base_url"],
            "Python.Version": __import__("sys").version.split()[0],
        }
        with open(env_file, "w") as f:
            for k, v in props.items():
                f.write(f"{k}={v}\n")
