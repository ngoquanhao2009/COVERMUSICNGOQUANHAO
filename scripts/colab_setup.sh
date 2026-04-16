#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if ! command -v ffmpeg >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y ffmpeg
fi

echo "[OK] Colab environment is ready."
echo "Ví dụ train:"
echo "python -m covermusic.train --data /content/drive/MyDrive/COVERMUSIC/data --name myvoice --workdir /content/drive/MyDrive/COVERMUSIC/work"
echo "Ví dụ cover:"
echo "python -m covermusic.cover --song /content/drive/MyDrive/COVERMUSIC/songs/song.mp3 --model /content/drive/MyDrive/COVERMUSIC/models/myvoice.pth --index /content/drive/MyDrive/COVERMUSIC/models/myvoice.index --out /content/drive/MyDrive/COVERMUSIC/output/cover.mp3 --workdir /content/drive/MyDrive/COVERMUSIC/work"

