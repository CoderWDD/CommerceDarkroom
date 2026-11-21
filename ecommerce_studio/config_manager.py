import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "default_config.json"
USER_CONFIG_PATH = BASE_DIR / "user_config.json"


def _deep_merge(default_dict: dict, user_dict: dict) -> dict:
    """递归合并配置，确保 user_dict 缺失的键由 default_dict 补全，同时保护脱敏星号不覆盖原密钥"""
    merged = dict(default_dict)
    for key, value in user_dict.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            child = dict(merged[key])
            for k, v in value.items():
                # 关键防御：若传入的 api_key 包含星号掩码或为空，且既有配置中已有有效密钥，则保留原有密钥
                if k == "api_key" and ("*" in str(v) or not str(v).strip()):
                    if child.get("api_key") and not ("*" in str(child["api_key"])):
                        continue
                child[k] = v
            merged[key] = child
        else:
            merged[key] = value
    return merged


def load_config() -> Dict[str, Any]:
    """读取配置，若存在用户自定义配置则合并加载，否则加载默认配置"""
    if not DEFAULT_CONFIG_PATH.exists():
        raise FileNotFoundError(f"默认配置文件未找到: {DEFAULT_CONFIG_PATH}")

    with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
        default_cfg = json.load(f)

    if USER_CONFIG_PATH.exists():
        try:
            with open(USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
                config = _deep_merge(default_cfg, user_cfg)
        except Exception:
            config = default_cfg
    else:
        config = default_cfg

    # 如果系统环境变量中已有 key 且配置中为空，则自动补充
    if not config.get("gemini", {}).get("api_key") and os.environ.get("GEMINI_API_KEY"):
        config.setdefault("gemini", {})["api_key"] = os.environ["GEMINI_API_KEY"]
    if not config.get("openai", {}).get("api_key") and os.environ.get("OPENAI_API_KEY"):
        config.setdefault("openai", {})["api_key"] = os.environ["OPENAI_API_KEY"]

    apply_environment_keys(config)
    return config


def save_config(config: Dict[str, Any]) -> None:
    """原子化保存用户配置到 user_config.json"""
    USER_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=str(USER_CONFIG_PATH.parent), delete=False, encoding="utf-8") as tf:
        json.dump(config, tf, indent=2, ensure_ascii=False)
        temp_name = tf.name
    os.replace(temp_name, USER_CONFIG_PATH)
    apply_environment_keys(config)


def reset_to_defaults() -> Dict[str, Any]:
    """重置为默认配置并删除自定义 user_config.json"""
    if USER_CONFIG_PATH.exists():
        USER_CONFIG_PATH.unlink()
    return load_config()


def apply_environment_keys(config: Dict[str, Any]) -> None:
    """将配置中的 API Key 同步到系统环境变量"""
    active_provider = config.get("active_provider", "gemini")

    gemini_key = config.get("gemini", {}).get("api_key", "").strip()
    if gemini_key and "*" not in gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key

    openai_key = config.get("openai", {}).get("api_key", "").strip()
    if openai_key and "*" not in openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    openai_base = config.get("openai", {}).get("base_url", "").strip()
    if openai_base:
        os.environ["OPENAI_BASE_URL"] = openai_base

    if active_provider == "custom_openai":
        custom_key = config.get("custom_openai", {}).get("api_key", "").strip()
        if custom_key and "*" not in custom_key:
            os.environ["OPENAI_API_KEY"] = custom_key
        custom_base = config.get("custom_openai", {}).get("base_url", "").strip()
        if custom_base:
            os.environ["OPENAI_BASE_URL"] = custom_base
    elif active_provider == "ollama":
        ollama_key = config.get("ollama", {}).get("api_key", "").strip() or "ollama"
        os.environ["OPENAI_API_KEY"] = ollama_key
        ollama_base = config.get("ollama", {}).get("base_url", "").strip() or "http://localhost:11434/v1"
        os.environ["OPENAI_BASE_URL"] = ollama_base
