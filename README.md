# 🎵 AI Cover Music – Ngô Quân Hào

Trang web tạo **AI Cover nhạc & giọng hát** chất lượng cao, nhanh chóng và miễn phí.

---

## Tính năng

- 🎙️ **AI Voice Conversion** – Chuyển đổi giọng hát sang bất kỳ ca sĩ bằng RVC v2
- 🎼 **Tách nhạc nền** – Tách vocal khỏi nhạc nền tự động với Demucs
- 📁 **Upload đa dạng** – Hỗ trợ MP3, WAV, FLAC, OGG, M4A (tối đa 50MB)
- 🔗 **YouTube** – Tải audio trực tiếp từ URL YouTube
- 🎙️ **Ghi âm trực tiếp** – Ghi âm ngay trên trình duyệt
- ⚙️ **Tùy chỉnh cao** – Pitch, Index Ratio, Protect Breath, Reverb, định dạng xuất
- 📥 **Xuất chất lượng cao** – MP3 320kbps / WAV 48kHz / FLAC lossless
- 🌙 **Dark mode UI** – Giao diện đẹp, responsive cho mobile

---

## Cài đặt & Chạy

### Yêu cầu
- Python 3.10+
- `ffmpeg` (cần cho YouTube download)

### Cách chạy

```bash
# Clone repo
git clone https://github.com/ngoquanhao2009/COVERMUSICNGOQUANHAO.git
cd COVERMUSICNGOQUANHAO

# Cài dependencies Python
pip install -r requirements.txt

# Chạy backend
cd server
python app.py

# Mở trình duyệt
# http://localhost:5000
```

> **Dùng không cần backend:** Mở `index.html` trực tiếp trên trình duyệt để trải nghiệm UI đầy đủ (tính năng AI cần backend).

---

## Cấu trúc dự án

```
COVERMUSICNGOQUANHAO/
├── index.html              # Trang web chính
├── assets/
│   ├── css/style.css       # Giao diện
│   └── js/app.js           # Logic frontend
├── server/
│   └── app.py              # Flask backend API
├── requirements.txt        # Python dependencies
└── README.md
```

---

## API Endpoints

| Method | Path                 | Mô tả                       |
|--------|----------------------|-----------------------------|
| GET    | `/api/health`        | Kiểm tra server             |
| GET    | `/api/voices`        | Danh sách giọng AI          |
| POST   | `/api/upload`        | Upload file âm thanh        |
| POST   | `/api/convert`       | Bắt đầu chuyển đổi giọng    |
| GET    | `/api/jobs/<id>`     | Kiểm tra trạng thái job     |
| GET    | `/api/download/<id>` | Tải file kết quả            |
| POST   | `/api/fetch-youtube` | Tải audio từ YouTube URL    |

---

## Tích hợp AI thực tế

Để tích hợp AI thật, bạn cần:

1. **Replicate API** – Đăng ký tại [replicate.com](https://replicate.com) và lấy API key
2. **RVC Model** – Dùng model RVC v2 trên Replicate hoặc tự host
3. **Demucs** – `pip install demucs` để tách vocal/nhạc nền

---

## License

MIT © 2024 Ngô Quân Hào
