import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; env vars still work if set externally.

def _as_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}

SKIP_AUDIO_PROCESS = _as_bool("SKIP_AUDIO_PROCESS", False)
SKIP_CALL_PROCESS = _as_bool("SKIP_CALL_PROCESS", False)