import argparse
import subprocess
from pathlib import Path

from .rvc_runtime import candidate_infer_commands, ensure_rvc_repo, find_infer_script
from .utils import ensure_exists, require_binary, run_cmd


def _download_youtube(song: str, workdir: Path) -> Path:
    out = workdir / "youtube_song.%(ext)s"
    run_cmd(
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "wav",
            "--audio-quality",
            "0",
            "-o",
            str(out),
            song,
        ]
    )
    candidates = sorted(workdir.glob("youtube_song.*"))
    if not candidates:
        raise RuntimeError("Failed to download song from YouTube URL.")
    return candidates[0]


def _separate(song: Path, workdir: Path) -> tuple[Path, Path]:
    separate_dir = workdir / "separated"
    run_cmd(
        [
            "python",
            "-m",
            "demucs.separate",
            "-n",
            "htdemucs",
            "--two-stems=vocals",
            "-o",
            str(separate_dir),
            str(song),
        ]
    )
    stem = song.stem
    vocals = separate_dir / "htdemucs" / stem / "vocals.wav"
    no_vocals = separate_dir / "htdemucs" / stem / "no_vocals.wav"
    ensure_exists(vocals, "vocal track")
    ensure_exists(no_vocals, "instrumental track")
    return vocals, no_vocals


def _run_rvc(
    vocals: Path,
    out_vocal: Path,
    model: Path,
    index: Path | None,
    pitch: int,
    index_rate: float,
    protect: float,
    f0_method: str,
    rvc_dir: Path,
) -> Path:
    infer_script = find_infer_script(rvc_dir)
    errors: list[str] = []
    for cmd in candidate_infer_commands(
        infer_script, vocals, out_vocal, model, index, pitch, index_rate, protect, f0_method
    ):
        try:
            run_cmd(cmd, cwd=rvc_dir)
            if out_vocal.exists():
                return out_vocal
        except subprocess.CalledProcessError as exc:
            errors.append(f"{cmd[0]} ... -> {exc}")
    raise RuntimeError("RVC inference failed with detected command templates.\n" + "\n".join(errors))


def _mix(instrumental: Path, converted_vocal: Path, out_file: Path) -> None:
    run_cmd(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(instrumental),
            "-i",
            str(converted_vocal),
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:normalize=0",
            "-c:a",
            "libmp3lame" if out_file.suffix.lower() == ".mp3" else "pcm_s16le",
            str(out_file),
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Create AI cover from a song and an RVC model.")
    p.add_argument("--song", required=True, help="Song file path or YouTube URL")
    p.add_argument("--model", required=True, help="Path to RVC .pth model")
    p.add_argument("--index", help="Path to RVC .index file")
    p.add_argument("--out", required=True, help="Output file path (.mp3 or .wav)")
    p.add_argument("--pitch", type=int, default=0)
    p.add_argument("--index-rate", type=float, default=0.75)
    p.add_argument("--protect", type=float, default=0.33)
    p.add_argument("--f0-method", default="rmvpe")
    p.add_argument("--workdir", default="/tmp/covermusic_work")
    p.add_argument("--rvc-dir", help="Path to preinstalled RVC repo")
    p.add_argument("--rvc-repo-url", default=None, help="Custom RVC repo URL")
    return p


def main() -> None:
    args = build_parser().parse_args()
    require_binary("ffmpeg")
    require_binary("git")
    require_binary("yt-dlp")

    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    out_file = Path(args.out).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    model = ensure_exists(Path(args.model).resolve(), "RVC model")
    index = Path(args.index).resolve() if args.index else None
    if index:
        ensure_exists(index, "RVC index")

    song_arg = args.song.strip()
    if song_arg.startswith(("http://", "https://")):
        song = _download_youtube(song_arg, workdir)
    else:
        song = ensure_exists(Path(song_arg).resolve(), "song file")

    vocals, no_vocals = _separate(song, workdir)
    converted_vocal = workdir / "converted_vocal.wav"
    rvc_dir = (
        ensure_exists(Path(args.rvc_dir).resolve(), "RVC repo")
        if args.rvc_dir
        else ensure_rvc_repo(workdir, repo_url=args.rvc_repo_url)
    )
    _run_rvc(
        vocals=vocals,
        out_vocal=converted_vocal,
        model=model,
        index=index,
        pitch=args.pitch,
        index_rate=args.index_rate,
        protect=args.protect,
        f0_method=args.f0_method,
        rvc_dir=rvc_dir,
    )
    _mix(no_vocals, converted_vocal, out_file)
    print(f"[OK] Cover created: {out_file}")


if __name__ == "__main__":
    main()
