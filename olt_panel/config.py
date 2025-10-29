from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal

import yaml
from pydantic import BaseModel, Field


class OLTDeviceConfig(BaseModel):
    name: str
    host: str
    port: int = 22
    protocol: Literal["ssh", "telnet"] = Field(default="ssh", description="Transport protocol")
    username: str
    password: str
    driver: str = Field(default="zte_c300_v2", description="Driver key, e.g. zte_c300_v2")
    prompt_regex: Optional[str] = Field(default=None, description="Custom prompt regex to detect command completion")
    ssh_timeout_s: int = Field(default=15, description="SSH read timeout in seconds")


class AppConfig(BaseModel):
    devices: list[OLTDeviceConfig] = Field(default_factory=list)


def _load_yaml(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def find_config_file() -> Optional[Path]:
    candidates = [
        Path.cwd() / "config.yml",
        Path.cwd() / "config.yaml",
        Path(__file__).resolve().parent.parent / "config.yml",
        Path(__file__).resolve().parent.parent / "config.yaml",
        Path(__file__).resolve().parent.parent / "config.example.yml",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def load_config() -> AppConfig:
    cfg_path = find_config_file()
    raw = _load_yaml(cfg_path) if cfg_path else None
    if raw is None:
        return AppConfig()
    try:
        return AppConfig(**raw)
    except Exception as ex:  # Keep simple, surface error clearly
        # Re-raise with context
        raise RuntimeError(f"Invalid configuration at {cfg_path}: {ex}")


# Eager load a global configuration instance
CONFIG = load_config()


def get_config() -> AppConfig:
    return CONFIG
