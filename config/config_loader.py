"""配置加载：按 ENV 环境变量读取 config.yaml 中对应环境配置。

优先级（高 → 低）:
  1. config.local.yaml   （本地覆盖敏感字段，已 gitignore）
  2. config.yaml[env]    （环境配置）
支持 ${VAR} 占位符，从系统环境变量取值。
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent
_MAIN = CONFIG_DIR / "config.yaml"
_LOCAL = CONFIG_DIR / "config.local.yaml"
_PLACEHOLDER = re.compile(r"\$\{(\w+)\}")


def _expand(value):
    """递归把 ${VAR} 替换成 os.environ[VAR]，缺失则保留原值。"""
    if isinstance(value, str):
        return _PLACEHOLDER.sub(lambda m: os.environ.get(m.group(1), m.group(0)), value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


@lru_cache(maxsize=None)
def get_config() -> dict:
    """返回当前环境配置 dict（带 local 覆盖 + 环境变量展开）。

    TODO: 你来实现。提示：
      1. 读 _MAIN (config.yaml)，yaml.safe_load
      2. 从 os.environ 取 ENV，没有就用 cfg['default_env']
      3. 从 cfg['envs'] 取对应环境 dict，浅拷贝
      4. 在浅拷贝里加一个 _env 字段记录当前环境名（后面 allure 报告要用）
      5. 如果 _LOCAL 存在，读它，按环境深合并一层（dict 套 dict 就合并，非 dict 直接覆盖）
      6. 调 _expand 展开占位符后返回
    """
    # ====== 以下留给你写 ======
    with open(_MAIN, 'r', encoding='utf-8') as file:
        cfg = yaml.safe_load(file)
        print(cfg)
        current_env = os.environ.get('ENV', cfg['default_env'])
        env_config = cfg['envs'][current_env].copy()
        env_config['_env']=current_env
        local_all=(yaml.safe_load(_LOCAL.read_text(encoding='utf-8')) or {})if _LOCAL.exists() else {}
        local_env=local_all.get(current_env, {})
        for k, v in local_env.items():
            if isinstance(v, dict) and isinstance(env_config.get(k), dict):
                # 两边都是 dict → 进去合并字段，不整段替换
                env_config[k] = {**env_config[k], **v}
            else:
                # 否则直接覆盖
                env_config[k] = v    
    return  _expand(env_config)


@lru_cache(maxsize=None)
def get_base_url() -> str:
    """便捷函数：直接拿 base_url，去掉末尾斜杠。"""
    return get_config()["base_url"].rstrip("/")
