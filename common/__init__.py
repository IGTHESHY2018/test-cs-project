"""common 包：日志配置 + 请求客户端。"""
import logging
import sys

from common.request import ApiClient, ApiResponseError, client

# 统一日志格式（写到 stderr）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    stream=sys.stderr,
)

__all__ = ["ApiClient", "ApiResponseError", "client"]
