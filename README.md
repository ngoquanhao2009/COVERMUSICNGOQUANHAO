# 🎵 AI Cover Music – Ngô Quân Hào

Repo đã được nâng cấp để chạy 2 chế độ trên Google Colab:

1) **Train** model giọng từ dataset của bạn (`.pth` + `.index`)  
2) **Cover/Inference** từ file nhạc hoặc YouTube URL

> ⚠️ Chỉ dùng giọng nói/giọng hát bạn có quyền sử dụng. Tôn trọng bản quyền bài hát và quyền nhân thân giọng nói.

---

## 1) Cài nhanh trên Colab (ưu tiên ít lệnh)

### Cell 1: clone + mount Drive + setup

```python
from google.colab import drive
drive.mount('/content/drive')
```

```bash
!git clone https://github.com/ngoquanhao2009/COVERMUSICNGOQUANHAO.git
%cd COVERMUSICNGOQUANHAO
!bash scripts/colab_setup.sh
```

---

## 2) Chuẩn bị dataset train giọng

- Khuyến nghị: **15–60 phút** audio sạch (ít ồn, ít reverb, ít nhạc nền)
- Tối thiểu có thể train từ 10 phút, nhưng chất lượng thường kém ổn định hơn
- Định dạng: wav/mp3/flac/ogg/m4a/aac
- Nếu mục tiêu cover hát, nên có một phần audio hát thật của chính bạn

### Gợi ý cấu trúc Google Drive

```text
MyDrive/COVERMUSIC/
├── data/
│   └── myvoice_dataset/        # dữ liệu train
├── work/                       # runtime train/infer
├── models/                     # chứa .pth/.index sau train
├── songs/
│   └── song.mp3
└── output/
```

---

## 3) Lệnh Train (CLI)

```bash
python -m covermusic.train \
  --data /content/drive/MyDrive/COVERMUSIC/data/myvoice_dataset \
  --name myvoice_v1 \
  --workdir /content/drive/MyDrive/COVERMUSIC/work \
  --epochs 200 \
  --sample-rate 40k \
  --f0-method rmvpe
```

Sau khi train xong, model thường nằm trong thư mục:

```text
/content/drive/MyDrive/COVERMUSIC/work/logs/myvoice_v1/
```

Hãy copy `.pth` + `.index` vào `MyDrive/COVERMUSIC/models/`.

---

## 4) Lệnh Cover/Inference (CLI)

### 4.1 Cover từ file nhạc

```bash
python -m covermusic.cover \
  --song /content/drive/MyDrive/COVERMUSIC/songs/song.mp3 \
  --model /content/drive/MyDrive/COVERMUSIC/models/myvoice_v1.pth \
  --index /content/drive/MyDrive/COVERMUSIC/models/myvoice_v1.index \
  --out /content/drive/MyDrive/COVERMUSIC/output/cover.mp3 \
  --workdir /content/drive/MyDrive/COVERMUSIC/work \
  --pitch 0 \
  --index-rate 0.75 \
  --protect 0.33
```

### 4.2 Cover từ YouTube URL

```bash
python -m covermusic.cover \
  --song "https://www.youtube.com/watch?v=VIDEO_ID" \
  --model /content/drive/MyDrive/COVERMUSIC/models/myvoice_v1.pth \
  --index /content/drive/MyDrive/COVERMUSIC/models/myvoice_v1.index \
  --out /content/drive/MyDrive/COVERMUSIC/output/cover_from_youtube.mp3 \
  --workdir /content/drive/MyDrive/COVERMUSIC/work
```

---

## 5) Chạy web backend Flask trên Colab

```bash
%cd /content/COVERMUSICNGOQUANHAO/server
!python app.py
```

### Expose public URL (tuỳ chọn)

#### Cloudflared

```bash
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb
!cloudflared tunnel --url http://localhost:5000
```

#### Ngrok

```bash
!pip install -q pyngrok
!ngrok config add-authtoken YOUR_NGROK_TOKEN
!ngrok http 5000
```

---

## 6) API backend thật cho `/api/convert`

`server/app.py` hiện hỗ trợ 2 mode:

- **Demo mode** (mặc định): mô phỏng
- **Real mode**: khi gửi thêm `model_name` (và tùy chọn `index_name`)

Model sẽ được đọc trong thư mục `COVERMUSIC_MODEL_DIR` (mặc định `/tmp/covermusic_models`) để tránh path traversal.

Ví dụ payload:

```json
{
  "file_id": "uuid",
  "ext": "mp3",
  "voice_id": "custom",
  "model_name": "myvoice_v1",
  "index_name": "myvoice_v1",
  "pitch": 0,
  "index_ratio": 0.75,
  "protect": 0.33,
  "output_format": "mp3"
}
```

---

## 7) Cấu trúc dự án chính

```text
COVERMUSICNGOQUANHAO/
├── covermusic/
│   ├── train.py              # python -m covermusic.train
│   ├── cover.py              # python -m covermusic.cover
│   └── rvc_runtime.py        # wrapper clone/call RVC runtime
├── scripts/
│   └── colab_setup.sh
├── server/
│   └── app.py
└── requirements.txt
```

---

## License

MIT © 2024 Ngô Quân Hào
