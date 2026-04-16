import re
import shutil
import subprocess
from pathlib import Path


_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def safe_name(value: str) -> str:
    cleaned = _SAFE_NAME_RE.sub("-", (value or "").strip())
    cleaned = cleaned.strip("-.")
    return cleaned or "model"


def ensure_exists(path: Path, kind: str = "path") -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{kind} not found: {path}")
    return path


def require_binary(name: str) -> None:
    if shutil.which(name):
        return
    raise RuntimeError(
        f"Missing dependency '{name}'. On Colab run scripts/colab_setup.sh first."
    )


def run_cmd(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)

