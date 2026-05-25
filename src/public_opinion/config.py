from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


ENV_FILE_ENV_VAR = "PUBLIC_OPINION_ENV_FILE"
OPENAI_BASE_URL_ENV_VAR = "PUBLIC_OPINION_OPENAI_BASE_URL"
OPENAI_API_KEY_ENV_VAR = "PUBLIC_OPINION_OPENAI_API_KEY"
OPENAI_MODEL_ENV_VAR = "PUBLIC_OPINION_OPENAI_MODEL"
OPENAI_TIMEOUT_SECONDS_ENV_VAR = "PUBLIC_OPINION_OPENAI_TIMEOUT_SECONDS"
DEFAULT_OPENAI_TIMEOUT_SECONDS = 30
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class OpenAISettings:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int


def get_openai_settings(
    *,
    base_url_override: str | None = None,
    model_override: str | None = None,
    timeout_seconds_override: int | None = None,
) -> OpenAISettings:
    load_env_file()
    return OpenAISettings(
        base_url=_resolve_required(base_url_override, OPENAI_BASE_URL_ENV_VAR),
        api_key=_resolve_required(None, OPENAI_API_KEY_ENV_VAR),
        model=_resolve_required(model_override, OPENAI_MODEL_ENV_VAR),
        timeout_seconds=_resolve_timeout(timeout_seconds_override),
    )


def load_env_file(env_path: Path | None = None) -> Path | None:
    path = env_path or _resolve_env_path()
    if not path.exists():
        return None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(raw_line)
        if parsed is None:
            continue
        key, value = parsed
        os.environ.setdefault(key, value)

    return path


def _resolve_env_path() -> Path:
    env_value = os.environ.get(ENV_FILE_ENV_VAR, "").strip()
    if env_value:
        return Path(env_value).expanduser().resolve()
    return PROJECT_ROOT / ".env"


def _parse_env_line(raw_line: str) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None

    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not key:
        return None

    if value and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return key, value


def _resolve_required(override: str | None, env_var_name: str) -> str:
    value = (override or "").strip()
    if value:
        return value

    env_value = os.environ.get(env_var_name, "").strip()
    if env_value:
        return env_value

    raise ValueError(f"Environment variable {env_var_name} is required")


def _resolve_timeout(timeout_seconds_override: int | None) -> int:
    if timeout_seconds_override is not None:
        return timeout_seconds_override

    env_value = os.environ.get(OPENAI_TIMEOUT_SECONDS_ENV_VAR, "").strip()
    if not env_value:
        return DEFAULT_OPENAI_TIMEOUT_SECONDS
    return int(env_value)
