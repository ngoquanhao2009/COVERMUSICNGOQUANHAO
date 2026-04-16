import os
from pathlib import Path

from .utils import ensure_exists, run_cmd


DEFAULT_RVC_REPO = "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git"


def ensure_rvc_repo(workdir: Path, repo_url: str | None = DEFAULT_RVC_REPO) -> Path:
    repo_dir = workdir / "rvc"
    if (repo_dir / ".git").exists():
        return repo_dir

    workdir.mkdir(parents=True, exist_ok=True)
    run_cmd(["git", "clone", "--depth=1", repo_url or DEFAULT_RVC_REPO, str(repo_dir)])
    return ensure_exists(repo_dir, "RVC repo")


def _pick_existing(repo_dir: Path, candidates: list[str]) -> Path:
    for rel in candidates:
        p = repo_dir / rel
        if p.exists():
            return p
    raise FileNotFoundError(
        "Cannot find expected RVC script in cloned repo. "
        "Please update repo or set --rvc-dir to a compatible RVC fork."
    )


def find_infer_script(repo_dir: Path) -> Path:
    return _pick_existing(
        repo_dir,
        [
            "tools/infer_cli.py",
            "tools/cmd/infer_cli.py",
        ],
    )


def find_train_scripts(repo_dir: Path) -> dict[str, Path]:
    return {
        "preprocess": _pick_existing(
            repo_dir,
            [
                "trainset_preprocess_pipeline_print.py",
                "infer/modules/train/preprocess.py",
            ],
        ),
        "extract_f0": _pick_existing(
            repo_dir,
            [
                "extract_f0_print.py",
                "infer/modules/train/extract/extract_f0_print.py",
            ],
        ),
        "extract_feature": _pick_existing(
            repo_dir,
            [
                "extract_feature_print.py",
                "infer/modules/train/extract_feature_print.py",
            ],
        ),
        "train": _pick_existing(
            repo_dir,
            [
                "train_nsf_sim_cache_sid_load_pretrain.py",
                "infer/modules/train/train.py",
            ],
        ),
        "index": _pick_existing(
            repo_dir,
            [
                "train_index.py",
                "infer/modules/train/train_index.py",
            ],
        ),
    }


def candidate_infer_commands(
    script: Path,
    song: Path,
    out_vocal: Path,
    model: Path,
    index: Path | None,
    pitch: int,
    index_rate: float,
    protect: float,
    f0_method: str,
) -> list[list[str]]:
    py = os.environ.get("PYTHON", "python")
    cmds = [
        [
            py,
            str(script),
            "--input_path",
            str(song),
            "--output_path",
            str(out_vocal),
            "--pth_path",
            str(model),
            "--f0method",
            f0_method,
            "--f0up_key",
            str(pitch),
            "--index_rate",
            str(index_rate),
            "--protect",
            str(protect),
        ],
        [
            py,
            str(script),
            str(song),
            str(out_vocal),
            str(model),
            str(index or ""),
            str(pitch),
            f0_method,
            str(index_rate),
            str(protect),
        ],
    ]
    if index:
        cmds[0].extend(["--index_path", str(index)])
    return cmds
