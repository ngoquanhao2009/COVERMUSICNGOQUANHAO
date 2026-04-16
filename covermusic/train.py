import argparse
import os
import subprocess
from pathlib import Path

from .rvc_runtime import ensure_rvc_repo, find_train_scripts
from .utils import ensure_exists, require_binary, run_cmd, safe_name


def _audio_files(data_dir: Path) -> list[Path]:
    exts = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
    return [p for p in data_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]


def _run_first_success(commands: list[list[str]], cwd: Path, step_name: str) -> None:
    errors: list[str] = []
    for cmd in commands:
        try:
            run_cmd(cmd, cwd=cwd)
            return
        except subprocess.CalledProcessError as exc:
            errors.append(f"{cmd[0]} ... -> {exc}")
    raise RuntimeError(f"{step_name} failed.\n" + "\n".join(errors))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train RVC model from your own voice dataset.")
    p.add_argument("--data", required=True, help="Directory containing voice dataset audio files")
    p.add_argument("--name", required=True, help="Model name")
    p.add_argument("--workdir", default="/tmp/covermusic_train")
    p.add_argument("--epochs", type=int, default=200)
    p.add_argument("--batch-size", type=int, default=6)
    p.add_argument("--sample-rate", default="40k", choices=["32k", "40k", "48k"])
    p.add_argument("--f0-method", default="rmvpe")
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--gpus", default="0", help="CUDA visible devices, e.g. 0 or 0-1")
    p.add_argument("--rvc-dir", help="Path to preinstalled RVC repo")
    p.add_argument("--rvc-repo-url", default=None, help="Custom RVC repo URL")
    return p


def main() -> None:
    args = build_parser().parse_args()
    require_binary("ffmpeg")
    require_binary("git")

    data_dir = ensure_exists(Path(args.data).resolve(), "dataset directory")
    files = _audio_files(data_dir)
    if not files:
        raise RuntimeError(f"No audio files found in dataset: {data_dir}")

    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    model_name = safe_name(args.name)
    exp_dir = (workdir / "logs" / model_name).resolve()
    exp_dir.mkdir(parents=True, exist_ok=True)

    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpus
    rvc_dir = (
        ensure_exists(Path(args.rvc_dir).resolve(), "RVC repo")
        if args.rvc_dir
        else ensure_rvc_repo(workdir, repo_url=args.rvc_repo_url)
    )
    scripts = find_train_scripts(rvc_dir)
    py = os.environ.get("PYTHON", "python")
    sr_num = {"32k": "32000", "40k": "40000", "48k": "48000"}[args.sample_rate]

    preprocess_cmds = [
        [py, str(scripts["preprocess"]), str(data_dir), sr_num, str(args.num_workers), str(exp_dir), "False"],
        [py, str(scripts["preprocess"]), str(data_dir), sr_num, str(args.num_workers), str(exp_dir)],
    ]
    _run_first_success(preprocess_cmds, cwd=rvc_dir, step_name="Preprocess")

    extract_f0_cmds = [
        [py, str(scripts["extract_f0"]), str(exp_dir), str(args.num_workers), args.f0_method],
        [py, str(scripts["extract_f0"]), str(exp_dir), args.f0_method],
    ]
    _run_first_success(extract_f0_cmds, cwd=rvc_dir, step_name="F0 extraction")

    extract_feature_cmds = [
        [py, str(scripts["extract_feature"]), "0", "0", str(args.num_workers), str(exp_dir), "v2"],
        [py, str(scripts["extract_feature"]), str(exp_dir), str(args.num_workers), "v2"],
    ]
    _run_first_success(extract_feature_cmds, cwd=rvc_dir, step_name="Feature extraction")

    train_cmds = [
        [
            py,
            str(scripts["train"]),
            "-e",
            model_name,
            "-sr",
            args.sample_rate,
            "-f0",
            "1",
            "-bs",
            str(args.batch_size),
            "-te",
            str(args.epochs),
            "-se",
            "10",
            "-l",
            "1",
            "-c",
            "0",
            "-v",
            "v2",
        ],
        [
            py,
            str(scripts["train"]),
            "--experiment_dir",
            str(exp_dir),
            "--epochs",
            str(args.epochs),
            "--batch_size",
            str(args.batch_size),
        ],
    ]
    _run_first_success(train_cmds, cwd=rvc_dir, step_name="Training")

    index_cmds = [
        [py, str(scripts["index"]), str(exp_dir), "v2"],
        [py, str(scripts["index"]), str(exp_dir)],
    ]
    _run_first_success(index_cmds, cwd=rvc_dir, step_name="Index build")

    pths = sorted(exp_dir.rglob("*.pth"), key=lambda p: p.stat().st_mtime, reverse=True)
    indexes = sorted(exp_dir.rglob("*.index"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not pths:
        raise RuntimeError(f"Training completed but no .pth found in {exp_dir}")

    print(f"[OK] Training done.\nModel: {pths[0]}")
    if indexes:
        print(f"Index: {indexes[0]}")
    print(f"Experiment folder: {exp_dir}")


if __name__ == "__main__":
    main()
