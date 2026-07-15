"""统一请求客户端：封装 requests.Session，统一超时/重试/日志/R 返回解析。

设计要点：
- 所有请求走 ApiClient，统一注入 base_url 与 Token header（由 conftest 注入）
- 统一超时；GET 幂等请求支持网络层重试
- 自动解析统一返回结构 R {code, msg, data}，业务失败抛 ApiResponseError
- 日志记录请求/响应摘要，便于排障
"""
from __future__ import annotations

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter

from config import get_base_url, get_config

logger = logging.getLogger("apifw")


class ApiResponseError(AssertionError):
    """业务层返回失败（R.code != success_code），继承 AssertionError 便于 pytest 断言。

    TODO: 你来实现。提示：
      - __init__ 接收 (code, msg, body) 三个参数，存为实例属性
      - 调 super().__init__(f"业务失败 code={code} msg={msg} body={body!r}")
        这样 pytest 报错时能直接看到这三个值
    """
    def __init__(self, code: Any, msg: str, body: dict):
        self.code = code
        self.msg = msg
        self.body = body
        super().__init__(f"业务失败 code={code} msg={msg} body={body!r}")


class ApiClient:
    """请求客户端；Token 由 conftest 通过 set_token 注入。"""

    def __init__(self):
        self._cfg = get_config()
        self.base_url = self._cfg["base_url"].rstrip("/")
        self._timeout = self._cfg["timeout"]
        self._retries = self._cfg.get("retries", 1)
        self._token: str | None = None
        self.session = requests.Session()
        # 网络层重试适配器（仅对幂等请求生效，requests 库自带机制）
        adapter = HTTPAdapter(max_retries=self._retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def set_token(self, token: str | None) -> None:
        """把 Token 注入 Session header，后续所有请求自动带上。

        TODO: 你来实现。提示：
          - 把 token 存到 self._token
          - 如果 token 非空，self.session.headers.update({"Token": token})
            注意：你被测项目读的是 "Token" 这个 header 名（不是 "Authorization"）
            来源：PRD/技术栈与业务流程图.md 第 318 行 "Header 携带 Token: <token>"
          - 如果 token 是 None，应该把 "Token" header 弹掉（避免上一个用例的 token 漏到下一个）
            提示：self.session.headers.pop("Token", None)
          - 加一行 logger.info 记录注入动作（token 打印前 12 字符即可，别打全量）
        """
        self._token = token
        if token:
            self.session.headers.update({"Token": token})
            logger.info(f"Token 注入: {token[:12]}...")
        else:
            self.session.headers.pop("Token", None)
            logger.info("Token 已清除")

    def request(self, method: str, path: str, *, params=None, json=None,
                data=None, headers=None, **kwargs) -> dict:
        """发送请求并解析返回 R。

        TODO: 你来实现。提示：
          1. 拼 URL：如果 path 以 http 开头就直接用，否则 f"{self.base_url}{path}"
          2. logger.info 记录请求摘要：方法、URL、params、json
          3. self.session.request(method, url, params=params, json=json, data=data,
                                  headers=headers, timeout=self._timeout, **kwargs)
          4. logger.info 记录响应摘要：status_code、url、resp.text[:500]（截断防刷屏）
          5. resp.raise_for_status()   # 4xx/5xx 直接抛
          6. body = resp.json()
          7. return self._unwrap(body)
        """
        if path.startswith("http"):
            url = path
        else:
            url=f"{self.base_url}{path}"
        logger.info(f"请求: {method} {url} params={params} json={json}")  
        resp=self.session.request(method, url, params=params, json=json, data=data,
                                  headers=headers, timeout=self._timeout, **kwargs)
        resp.raise_for_status()
        body=resp.json()
        logger.info(f"响应: {resp.status_code} {url} {resp.text[:500]}")
        return self._unwrap(body)
    
    def _unwrap(self, body: dict) -> dict:
        """解析统一返回 R；非 R 结构（无 code 字段）原样返回。

        TODO: 你来实现。提示：
          1. 从 self._cfg["response"] 取 code_field/msg_field/success_code
          2. 如果 body 不是 dict 或不含 code_field → 原样返回（非 R 结构交由用例断言）
          3. 如果 body[code_field] != success_code → raise ApiResponseError(code, msg, body)
             其中 msg 从 body[msg_field] 取，缺失则空串
          4. 否则返回 body
        """
        return body
        

    # ---- 便捷方法（我写好了，你不用动）----
    def get(self, path, **kw):     return self.request("GET", path, **kw)
    def post(self, path, **kw):    return self.request("POST", path, **kw)
    def put(self, path, **kw):     return self.request("PUT", path, **kw)
    def delete(self, path, **kw):  return self.request("DELETE", path, **kw)


# 进程级单例
client = ApiClient()
