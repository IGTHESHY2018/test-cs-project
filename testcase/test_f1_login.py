"""F1 登录用例 — 对应 data/f1_login.yaml

技术栈：pytest parametrize + yaml 数据驱动 + allure step + AAA 结构
每个 yaml case 驱动一次测试运行。
"""
from __future__ import annotations

from pathlib import Path

import allure
import pytest
import yaml

from apis import UsersApi, YonghuApi
from common import ApiResponseError

DATA_FILE = Path(__file__).parent.parent / "data" / "f1_login.yaml"


def _load_cases():
    with DATA_FILE.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return doc["cases"]


_cases = _load_cases()


@allure.feature("F1-身份与访问控制")
class TestF1Login:
    """登录接口测试：用户登录 / 管理员登录 / 正向 / 边界 / 异常"""

    # ============================================================
    # 核心逻辑留给你
    # ============================================================

    @pytest.mark.parametrize("case", _cases, ids=[c["id"] for c in _cases])
    def test_login(self, case):
        """按 yaml 用例驱动登录测试。"""
        with allure.step(f"{case['id']} — {case['title']}"):
            # ---- Arrange ----
            # 根据 api 字段选择 API 类：yonghu → YonghuApi，users → UsersApi
            # TODO 你写：if case["api"] == "yonghu": api = YonghuApi()
            #          else: api = UsersApi()
            if case["api"]=="yonghu":
                api=YonghuApi()
            else:
                api=UsersApi()

            # ---- Act ----
            params = case["params"]
            resp = api.login(
                username=params.get("username"),
                password=params.get("password"),
            )

            # ---- Assert ----
            expected = case["expect"]

            # 1) 校验 code
            # TODO 你写：assert resp["code"] == expected["code"], ...
            assert resp["code"]==expected["code"],f"期望 code={expected['code']}，实际 code={resp['code']}"

            # 2) 如果期望有 token，校验 token 存在且非空
            # TODO 你写：if expected.get("has_token"): assert resp.get("token"), ...
            if expected.get("has_token"):
                assert resp.get("token"), f"期望有 token，但实际没有"

            # 3) 如果期望 msg 包含特定文本，校验 msg
            # TODO 你写：if "msg_contains" in expected: assert expected["msg_contains"] in resp.get("msg", ""), ...
            if "msg_contains" in expected:
                assert expected["msg_contains"] in resp.get("msg", ""), f"期望 msg 包含 '{expected['msg_contains']}'，但实际 msg 是 '{resp.get('msg', '')}'"
