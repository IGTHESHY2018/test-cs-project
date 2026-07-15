"""API 层基类：封装项目里 12 个控制器共享的 CRUD 套路。

实测接口风格（已通过 curl 验证）：
  - page:  GET  /{res}/page?page=1&limit=10&...过滤  分页查询
  - list:  GET  /{res}/list                         全量列表（不分页）
  - info:  GET  /{res}/info/{id}                    单条详情
  - save:  POST /{res}/save                         新增/保存
  - update:POST /{res}/update                       修改
  - delete:POST /{res}/delete   body=[id]           删除

特殊：租赁订单控制器用 /add 而非 /save，/detail/{id} 而非 /info/{id}
子类覆盖对应方法即可。
"""
from __future__ import annotations

from common import client


class BaseApi:
    resource: str = ""  # 子类覆盖，如 "/cheliangxinxi"

    def __init__(self, _client=client):
        self.client = _client

    def _path(self, action: str) -> str:
        return f"{self.resource}/{action}"

    # ---- 以下留给核心部分你自己写 ----

    def page(self, page: int = 1, limit: int = 10, **filters):
        """分页查询，GET 请求，过滤条件拼进 query string。"""
        return self.client.get(self._path("page"), params={"page": page, "limit": limit, **filters})

    def list(self, **filters):
        """全量列表，GET 请求。"""
        return self.client.get(self._path("list"), params=filters)

    def info(self, id):
        """单条详情，GET /{res}/info/{id}。"""
        return self.client.get(self._path("info") + f"/{id}")

    def save(self, payload: dict):
        """新增，POST JSON body。"""
        return self.client.post(self._path("save"), json=payload)

    def update(self, payload: dict):
        """修改，POST JSON body。"""
        return self.client.post(self._path("update"), json=payload)

    def delete(self, id):
        """删除，POST body=[id]（注意 body 是数组，不是 {"id":id}）。"""
        return self.client.post(self._path("delete"), json=[id])
