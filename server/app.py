"""
AI Cover Music – Flask Backend
Handles audio uploads, YouTube download, and AI voice conversion (demo + real pipeline option).
"""

import os
import re
import uuid
import shutil
import threading
import time
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import safe_join
from flask_cors import CORS

app = Flask(__name__, static_folder="..", static_url_path="")
CORS(app)

# ---------- Configuration ----------
UPLOAD_FOLDER = Path("/tmp/ai_cover_uploads")
RESULT_FOLDER = Path("/tmp/ai_cover_results")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
RESULT_FOLDER.mkdir(parents=True, exist_ok=True)
MODEL_FOLDER = Path(os.environ.get("COVERMUSIC_MODEL_DIR", "/tmp/covermusic_models")).resolve()
MODEL_FOLDER.mkdir(parents=True, exist_ok=True)
PIPELINE_WORKDIR = Path(os.environ.get("COVERMUSIC_PIPELINE_WORKDIR", "/tmp/covermusic_pipeline")).resolve()
PIPELINE_WORKDIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"mp3", "wav", "flac", "ogg", "m4a", "aac"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# UUID v4 pattern
_UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)

# Server-side registries – paths are stored here and never reconstructed from user input
uploaded_files: dict[str, dict] = {}   # {file_id: {"path": str, "ext": str}}
jobs: dict[str, dict]           = {}   # {job_id: {..., "result_path": str}}

# ---------- Helpers ----------

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_ext(ext: str) -> str:
    """Return ext only if it is in the allowed set, else raise ValueError."""
    clean = ext.lower().strip()
    if clean not in ALLOWED_EXTENSIONS:
        raise ValueError("Extension not allowed")
    return clean


def validate_uuid(value: str) -> str:
    """Return value if it is a valid UUID v4, else raise ValueError."""
    v = str(value).lower().strip()
    if not _UUID4_RE.match(v):
        raise ValueError("Invalid ID")
    return v


def make_upload_path(file_id: str, ext: str) -> Path:
    """Return a server-chosen path for an uploaded file (both components server-generated)."""
    return UPLOAD_FOLDER / f"{file_id}.{ext}"


def make_result_path(job_id: str, ext: str) -> Path:
    """Return a server-chosen path for a conversion result (both components server-generated)."""
    return RESULT_FOLDER / f"{job_id}.{ext}"


def cleanup_file(path: str, delay: int = 3600):
    """Delete a file after `delay` seconds (default 1 hour)."""
    def _delete():
        time.sleep(delay)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
    threading.Thread(target=_delete, daemon=True).start()


def resolve_model_path(model_name: str, expected_ext: str) -> Path:
    """
    Resolve a model/index path using only a sanitized filename inside MODEL_FOLDER.
    Prevents path traversal and avoids exposing server internal layout.
    """
    cleaned = secure_filename(model_name or "").strip()
    if not cleaned:
        raise ValueError("Invalid model name")

    p = Path(cleaned)
    if p.suffix:
        stem = p.stem
    else:
        stem = cleaned
    filename = f"{stem}.{expected_ext}"
    resolved = (MODEL_FOLDER / filename).resolve()
    if not resolved.is_relative_to(MODEL_FOLDER):
        raise ValueError("Invalid model path")
    return resolved


def parse_int(value, default: int, minimum: int = -24, maximum: int = 24) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(min(parsed, maximum), minimum)


def parse_float(value, default: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(min(parsed, maximum), minimum)


# ---------- Routes ----------

@app.route("/")
def index():
    """Serve the frontend index page."""
    root = Path("..").resolve()
    index_path = (root / "index.html").resolve()
    if not index_path.is_relative_to(root):
        return "Forbidden", 403
    return send_file(str(index_path))


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


@app.route("/api/voices")
def get_voices():
    """Return available AI voice models."""
    voices = [
        {"id": "son-tung",     "name": "Son Tung M-TP",  "emoji": "\U0001f3a4", "cat": "vn",    "tags": "Pop, Ballad"},
        {"id": "huong-ly",     "name": "Huong Ly",        "emoji": "\U0001f3b5", "cat": "vn",    "tags": "Ballad, OST"},
        {"id": "han-sara",     "name": "Han Sara",         "emoji": "\U0001f338", "cat": "vn",    "tags": "Pop, K-Pop"},
        {"id": "hoang-dung",   "name": "Hoang Dung",       "emoji": "\U0001f3b8", "cat": "vn",    "tags": "Indie, Soul"},
        {"id": "duc-phuc",     "name": "Duc Phuc",         "emoji": "\U0001f31f", "cat": "vn",    "tags": "Ballad, Pop"},
        {"id": "bts-jungkook", "name": "Jungkook (BTS)",   "emoji": "\U0001f430", "cat": "kpop",  "tags": "K-Pop, RnB"},
        {"id": "iu",           "name": "IU",               "emoji": "\U0001f319", "cat": "kpop",  "tags": "K-Pop, Ballad"},
        {"id": "taylor",       "name": "Taylor Swift",     "emoji": "\U0001f98b", "cat": "us",    "tags": "Pop, Country"},
        {"id": "ariana",       "name": "Ariana Grande",    "emoji": "\U0001f380", "cat": "us",    "tags": "Pop, RnB"},
        {"id": "hatsune",      "name": "Hatsune Miku",     "emoji": "\U0001f499", "cat": "anime", "tags": "Vocaloid"},
    ]
    return jsonify(voices)


@app.route("/api/upload", methods=["POST"])
def upload_audio():
    """Upload an audio file and return a temporary file ID."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    try:
        ext = sanitize_ext(file.filename.rsplit(".", 1)[1])
    except ValueError:
        return jsonify({"error": "File type not allowed"}), 400

    # Both file_id and ext are server-determined; no user input reaches the path
    file_id   = str(uuid.uuid4())
    save_path = make_upload_path(file_id, ext)
    file.save(str(save_path))
    cleanup_file(str(save_path))

    # Register server-side so /api/convert can look up the real path
    uploaded_files[file_id] = {"path": str(save_path), "ext": ext}

    return jsonify({"file_id": file_id, "ext": ext, "size": save_path.stat().st_size})


@app.route("/api/convert", methods=["POST"])
def convert_voice():
    """
    Start an AI voice conversion job.

    Expected JSON body:
    {
        "file_id":       "<uuid>",
        "ext":           "mp3",
        "voice_id":      "son-tung",
        "pitch":         0,
        "index_ratio":   0.75,
        "protect":       0.33,
        "separate":      true,
        "reverb":        false,
        "output_format": "mp3"
    }

    In production this would:
      1. Retrieve the uploaded file from the server-side registry
      2. Call Demucs (if separate=true) to split vocal/instrumental
      3. Call an RVC v2 model via Replicate API
      4. Mix converted vocal back with instrumental
      5. Return a job_id for polling

    This demo version returns a simulated job that resolves after a delay.
    """
    data = request.get_json(force=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body"}), 400
    for field in ("file_id", "ext", "voice_id"):
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    try:
        file_id = validate_uuid(data["file_id"])
    except ValueError:
        return jsonify({"error": "Invalid file ID"}), 400

    # Look up the real path from the server-side registry (no user-supplied path)
    record = uploaded_files.get(file_id)
    if not record or not Path(record["path"]).exists():
        return jsonify({"error": "Uploaded file not found. Please re-upload."}), 404

    # Validate requested output format (optional, fall back to source ext)
    raw_fmt = data.get("output_format", record["ext"])
    try:
        output_ext = sanitize_ext(raw_fmt)
    except ValueError:
        output_ext = record["ext"]

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "queued", "progress": 0, "message": "Dang xep hang..."}

    model_name = str(data.get("model_name", "")).strip()
    index_name = str(data.get("index_name", "")).strip()
    use_real_pipeline = bool(model_name)

    if use_real_pipeline:
        try:
            model_path = resolve_model_path(model_name, "pth")
            index_path = resolve_model_path(index_name, "index") if index_name else None
        except ValueError:
            return jsonify({"error": "Invalid model_name/index_name"}), 400

        if not model_path.exists():
            return jsonify({"error": "Model not found on server"}), 404
        if index_path and not index_path.exists():
            return jsonify({"error": "Index not found on server"}), 404

        threading.Thread(
            target=_run_real_conversion,
            args=(
                job_id,
                record["path"],
                str(model_path),
                str(index_path) if index_path else "",
                output_ext,
                parse_int(data.get("pitch", 0), default=0),
                parse_float(data.get("index_ratio", 0.75), default=0.75),
                parse_float(data.get("protect", 0.33), default=0.33),
            ),
            daemon=True,
        ).start()
    else:
        # Start async simulation (fallback demo mode)
        threading.Thread(
            target=_run_conversion,
            args=(job_id, record["path"], data.get("voice_id", ""), output_ext),
            daemon=True,
        ).start()

    return jsonify({"job_id": job_id})


def _run_conversion(job_id: str, src_path: str, voice_id: str, output_ext: str):
    """Simulate the conversion pipeline. Replace with real AI calls."""
    stages = [
        (0.10, "Dang upload len GPU server..."),
        (0.30, "Tach vocal va nhac nen (Demucs)..."),
        (0.75, "AI chuyen doi giong (RVC v2)..."),
        (0.90, "Ghep nhac nen..."),
        (1.00, "Xuat file..."),
    ]
    for progress, message in stages:
        time.sleep(1.5)
        jobs[job_id] = {"status": "processing", "progress": progress, "message": message}

    # Both job_id and output_ext are server-determined; no user input reaches the path
    result_path = make_result_path(job_id, output_ext)
    shutil.copy2(src_path, str(result_path))
    cleanup_file(str(result_path))

    jobs[job_id] = {
        "status":      "done",
        "progress":    1.0,
        "message":     "Hoan thanh!",
        "result_id":   job_id,
        "ext":         output_ext,
        # Store the real path server-side; download route uses this directly
        "result_path": str(result_path),
    }


def _run_real_conversion(
    job_id: str,
    src_path: str,
    model_path: str,
    index_path: str,
    output_ext: str,
    pitch: int,
    index_ratio: float,
    protect: float,
):
    """
    Run real conversion via CLI module: python -m covermusic.cover ...
    If it fails, job is marked as error without exposing internal server paths.
    """
    jobs[job_id] = {"status": "processing", "progress": 0.1, "message": "Khoi dong pipeline that..."}

    result_path = make_result_path(job_id, output_ext)
    cmd = [
        os.environ.get("PYTHON", "python"),
        "-m",
        "covermusic.cover",
        "--song",
        src_path,
        "--model",
        model_path,
        "--out",
        str(result_path),
        "--workdir",
        str(PIPELINE_WORKDIR / job_id),
        "--pitch",
        str(pitch),
        "--index-rate",
        str(index_ratio),
        "--protect",
        str(protect),
    ]
    if index_path:
        cmd.extend(["--index", index_path])

    try:
        subprocess.run(cmd, check=True)
    except Exception:
        jobs[job_id] = {
            "status": "error",
            "progress": 0,
            "message": "Pipeline loi. Kiem tra model, ffmpeg, demucs va RVC runtime.",
        }
        return

    if not result_path.exists():
        jobs[job_id] = {
            "status": "error",
            "progress": 0,
            "message": "Khong tim thay file ket qua sau khi convert.",
        }
        return

    cleanup_file(str(result_path))
    jobs[job_id] = {
        "status": "done",
        "progress": 1.0,
        "message": "Hoan thanh!",
        "result_id": job_id,
        "ext": output_ext,
        "result_path": str(result_path),
    }


@app.route("/api/jobs/<job_id>")
def job_status(job_id: str):
    """Poll conversion job status."""
    try:
        job_id = validate_uuid(job_id)
    except ValueError:
        return jsonify({"error": "Invalid job ID"}), 400

    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    # Never expose the internal result_path to the client
    public = {k: v for k, v in job.items() if k != "result_path"}
    return jsonify(public)


@app.route("/api/download/<job_id>")
def download_result(job_id: str):
    """Download the converted audio file."""
    try:
        job_id = validate_uuid(job_id)
    except ValueError:
        return jsonify({"error": "Invalid job ID"}), 400

    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        return jsonify({"error": "Result not ready"}), 404

    # Use the server-stored path directly – no path reconstruction from user input
    result_path_str = job.get("result_path", "")
    result_path = Path(result_path_str)
    if not result_path.exists():
        return jsonify({"error": "File not found or expired"}), 404

    ext = job.get("ext", "mp3")
    return send_file(
        str(result_path),
        mimetype=f"audio/{ext}",
        as_attachment=True,
        download_name=f"ai_cover_{job_id[:8]}.{ext}",
    )


@app.route("/api/fetch-youtube", methods=["POST"])
def fetch_youtube():
    """
    Download audio from a YouTube URL.
    Requires yt-dlp to be installed: pip install yt-dlp
    """
    data = request.get_json(force=True)
    raw_url = data.get("url", "").strip()
    if not raw_url:
        return jsonify({"error": "No URL provided"}), 400

    # Validate using URL parser – reject anything not on youtube.com / youtu.be
    try:
        parsed = urlparse(raw_url)
        hostname = parsed.hostname or ""
        # Strip www. / m. prefixes before comparing
        bare = re.sub(r"^(www\.|m\.)", "", hostname)
        if bare not in ("youtube.com", "youtu.be"):
            raise ValueError("Not a YouTube URL")
    except (ValueError, AttributeError):
        return jsonify({"error": "URL khong phai YouTube"}), 400

    try:
        import yt_dlp  # type: ignore
    except ImportError:
        return jsonify({"error": "yt-dlp chua duoc cai. Chay: pip install yt-dlp"}), 501

    file_id  = str(uuid.uuid4())
    out_path = make_upload_path(file_id, "mp3")   # server-generated path
    ydl_opts = {
        "format":         "bestaudio/best",
        "outtmpl":        str(out_path).replace(".mp3", ".%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}],
        "quiet":          True,
        "no_warnings":    True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info  = ydl.extract_info(raw_url, download=True)
        title = info.get("title", "YouTube Audio")

    if not out_path.exists():
        return jsonify({"error": "Tai xuong that bai"}), 500

    cleanup_file(str(out_path))
    uploaded_files[file_id] = {"path": str(out_path), "ext": "mp3"}
    return jsonify({"file_id": file_id, "ext": "mp3", "title": title, "size": out_path.stat().st_size})


# ---------- Serve static files ----------

@app.route("/<path:filename>")
def serve_static(filename: str):
    """Serve files from the project root (one level above server/)."""
    root = str(Path("..").resolve())
    # werkzeug.security.safe_join raises NotFound if the path escapes root
    safe = safe_join(root, filename)
    if safe is None or not Path(safe).is_file():
        return "Not found", 404
    return send_file(safe)


if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
