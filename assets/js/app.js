/* =====================================================
   AI Cover Music – App JavaScript
   ===================================================== */

// ===== Voice Data =====
const VOICES = [
  { id: "son-tung",    name: "Sơn Tùng M-TP", emoji: "🎤", cat: "vn",   tags: "Pop, Ballad" },
  { id: "huong-ly",    name: "Hương Ly",       emoji: "🎵", cat: "vn",   tags: "Ballad, OST" },
  { id: "han-sara",    name: "Han Sara",        emoji: "🌸", cat: "vn",   tags: "Pop, K-Pop" },
  { id: "hoang-dung",  name: "Hoàng Dũng",     emoji: "🎸", cat: "vn",   tags: "Indie, Soul" },
  { id: "duc-phuc",    name: "Đức Phúc",        emoji: "🌟", cat: "vn",   tags: "Ballad, Pop" },
  { id: "min",         name: "MIN",             emoji: "✨", cat: "vn",   tags: "Pop, RnB" },
  { id: "erik",        name: "ERIK",            emoji: "🎶", cat: "vn",   tags: "Pop, Ballad" },
  { id: "my-tam",      name: "Mỹ Tâm",          emoji: "👑", cat: "vn",   tags: "Pop, Queen" },
  { id: "bts-jungkook",name: "Jungkook (BTS)",  emoji: "🐰", cat: "kpop", tags: "K-Pop, RnB" },
  { id: "iu",          name: "IU",              emoji: "🌙", cat: "kpop", tags: "K-Pop, Ballad" },
  { id: "aespa-karina",name: "Karina (aespa)",  emoji: "🤖", cat: "kpop", tags: "K-Pop, Dance" },
  { id: "lim-jaebeom", name: "Jay B (GOT7)",    emoji: "🎙️", cat: "kpop", tags: "K-Pop, RnB" },
  { id: "taylor",      name: "Taylor Swift",    emoji: "🦋", cat: "us",   tags: "Pop, Country" },
  { id: "ariana",      name: "Ariana Grande",   emoji: "🎀", cat: "us",   tags: "Pop, RnB" },
  { id: "weekend",     name: "The Weeknd",      emoji: "🌃", cat: "us",   tags: "RnB, Pop" },
  { id: "ed-sheeran",  name: "Ed Sheeran",      emoji: "🎵", cat: "us",   tags: "Pop, Folk" },
  { id: "billie",      name: "Billie Eilish",   emoji: "🖤", cat: "us",   tags: "Alt, Pop" },
  { id: "doja",        name: "Doja Cat",        emoji: "🐱", cat: "us",   tags: "Pop, Rap" },
  { id: "hatsune",     name: "Hatsune Miku",    emoji: "💙", cat: "anime",tags: "Vocaloid" },
  { id: "ado",         name: "Ado",             emoji: "🎪", cat: "anime",tags: "Anime, J-Pop" },
  { id: "yoasobi",     name: "Ikura (YOASOBI)", emoji: "🌙", cat: "anime",tags: "J-Pop, Anime" },
  { id: "lisa",        name: "LiSA",            emoji: "⚔️", cat: "anime",tags: "Anime, Rock" },
];

// ===== State =====
let selectedFile  = null;
let selectedVoice = null;
let recordingStream = null;
let mediaRecorder  = null;
let recordedChunks = [];
let recordTimer    = null;
let recordSeconds  = 0;
let isRecording    = false;
let currentStep    = 1;
let simulatedResultBlob = null;

// ===== Init =====
document.addEventListener("DOMContentLoaded", () => {
  renderVoiceGrid(VOICES);
  initNavScroll();
  initHamburger();
  animateHeroBar();
});

// ===== Navbar =====
function initNavScroll() {
  const navbar = document.getElementById("navbar");
  window.addEventListener("scroll", () => {
    navbar.classList.toggle("scrolled", window.scrollY > 20);
  });
}

function initHamburger() {
  const btn = document.getElementById("hamburger");
  const links = document.querySelector(".nav-links");
  if (!btn || !links) return;
  btn.addEventListener("click", () => {
    links.classList.toggle("open");
    document.body.style.overflow = links.classList.contains("open") ? "hidden" : "";
  });
  links.addEventListener("click", (e) => {
    if (e.target.tagName === "A") {
      links.classList.remove("open");
      document.body.style.overflow = "";
    }
  });
}

// ===== Hero bar animation =====
function animateHeroBar() {
  const bar = document.getElementById("heroBar");
  if (!bar) return;
  let w = 0;
  const tick = setInterval(() => {
    w = Math.min(w + Math.random() * 5, 100);
    bar.style.width = w + "%";
    if (w >= 100) { clearInterval(tick); setTimeout(() => { w = 0; animateHeroBar(); }, 1500); }
  }, 80);
}

// ===== Scroll helpers =====
function scrollToStudio() {
  document.getElementById("studio").scrollIntoView({ behavior: "smooth" });
}

function playDemo() {
  showToast("🎵 Demo đang được phát… (tính năng demo sẽ sớm có!)");
}

// ===== Upload tabs =====
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const tabId = "tab-" + btn.dataset.tab;
      document.getElementById(tabId)?.classList.add("active");
    });
  });
});

// ===== Drag & Drop =====
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById("dropzone").classList.add("drag-over");
}
function handleDragLeave(e) {
  document.getElementById("dropzone").classList.remove("drag-over");
}
function handleDrop(e) {
  e.preventDefault();
  document.getElementById("dropzone").classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) loadFile(file);
}

// ===== File select =====
function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) loadFile(file);
}

function loadFile(file) {
  const allowed = ["audio/mpeg","audio/wav","audio/flac","audio/ogg","audio/mp4","audio/x-m4a","audio/aac"];
  if (!file.type.startsWith("audio/") && !allowed.some(t => file.name.toLowerCase().endsWith(t.split("/")[1]))) {
    showToast("❌ Vui lòng chọn file âm thanh hợp lệ (MP3, WAV, FLAC…)");
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    showToast("❌ File quá lớn! Tối đa 50MB.");
    return;
  }
  selectedFile = file;
  const url = URL.createObjectURL(file);
  document.getElementById("fileName").textContent = file.name;
  document.getElementById("fileSize").textContent = formatSize(file.size);
  document.getElementById("audioPreview").src = url;
  document.getElementById("filePreview").style.display = "block";
  document.getElementById("btn-step1-next").disabled = false;
  showToast("✅ File đã được tải lên thành công!");
}

function clearFile() {
  selectedFile = null;
  document.getElementById("audioFileInput").value = "";
  document.getElementById("filePreview").style.display = "none";
  document.getElementById("btn-step1-next").disabled = true;
}

// ===== YouTube fetch =====
function fetchYouTube() {
  const raw = document.getElementById("youtubeUrl").value.trim();
  let parsed;
  try {
    parsed = new URL(raw);
  } catch {
    showToast("❌ URL không hợp lệ!");
    return;
  }
  const host = parsed.hostname.replace(/^www\./, "");
  const isYouTube = host === "youtube.com" || host === "youtu.be";
  if (!isYouTube) {
    showToast("❌ URL YouTube không hợp lệ!");
    return;
  }
  showToast("⏳ Đang tải audio từ YouTube… (chức năng cần backend API)");
  // In a real deployment this would call the backend /api/fetch-youtube
}

// ===== Recording =====
function toggleRecord() {
  if (isRecording) stopRecord();
  else startRecord();
}

async function startRecord() {
  try {
    recordingStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(recordingStream);
    recordedChunks = [];
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) recordedChunks.push(e.data);
    };
    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: "audio/wav" });
      const f = new File([blob], `recording-${Date.now()}.wav`, { type: "audio/wav" });
      loadFile(f);
      goToPanel(1); // Switch back to file tab after recording
    };
    mediaRecorder.start();
    isRecording = true;
    recordSeconds = 0;
    document.getElementById("recordBtn").classList.add("recording");
    document.getElementById("recordLabel").textContent = "Dừng ghi âm";
    document.getElementById("liveVisualizer").style.display = "block";
    drawLiveWaveform(recordingStream);
    recordTimer = setInterval(() => {
      recordSeconds++;
      const mm = String(Math.floor(recordSeconds / 60)).padStart(2, "0");
      const ss = String(recordSeconds % 60).padStart(2, "0");
      document.getElementById("recordTimer").textContent = `${mm}:${ss}`;
    }, 1000);
  } catch {
    showToast("❌ Không thể truy cập microphone. Hãy cấp quyền.");
  }
}

function stopRecord() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    recordingStream.getTracks().forEach(t => t.stop());
  }
  clearInterval(recordTimer);
  isRecording = false;
  document.getElementById("recordBtn").classList.remove("recording");
  document.getElementById("recordLabel").textContent = "Bắt đầu ghi âm";
  document.getElementById("liveVisualizer").style.display = "none";
  document.getElementById("recordTimer").textContent = "00:00";
}

function drawLiveWaveform(stream) {
  const canvas = document.getElementById("liveCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const audioCtx = new AudioContext();
  const analyser = audioCtx.createAnalyser();
  audioCtx.createMediaStreamSource(stream).connect(analyser);
  analyser.fftSize = 256;
  const data = new Uint8Array(analyser.frequencyBinCount);

  function draw() {
    if (!isRecording) return;
    requestAnimationFrame(draw);
    analyser.getByteTimeDomainData(data);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    ctx.strokeStyle = "#7c3aed";
    ctx.lineWidth = 2;
    const step = canvas.width / data.length;
    data.forEach((v, i) => {
      const y = (v / 128.0) * (canvas.height / 2);
      i === 0 ? ctx.moveTo(0, y) : ctx.lineTo(i * step, y);
    });
    ctx.stroke();
  }
  draw();
}

// ===== Voice Grid =====
function renderVoiceGrid(list) {
  const grid = document.getElementById("voiceGrid");
  grid.innerHTML = list.map(v => `
    <div class="voice-card" data-id="${v.id}" data-cat="${v.cat}" onclick="selectVoice('${v.id}', this)">
      <div class="vc-avatar">${v.emoji}</div>
      <div class="vc-name">${v.name}</div>
      <div class="vc-tags">${v.tags}</div>
    </div>
  `).join("");
}

function selectVoice(id, el) {
  document.querySelectorAll(".voice-card").forEach(c => c.classList.remove("selected"));
  el.classList.add("selected");
  selectedVoice = VOICES.find(v => v.id === id);
  document.getElementById("btn-step2-next").disabled = false;
  showToast(`🎤 Đã chọn giọng: ${selectedVoice.name}`);
}

function filterVoices(query) {
  const q = query.toLowerCase();
  document.querySelectorAll(".voice-card").forEach(card => {
    const name = card.querySelector(".vc-name").textContent.toLowerCase();
    const tags = card.querySelector(".vc-tags").textContent.toLowerCase();
    card.classList.toggle("hidden", q && !name.includes(q) && !tags.includes(q));
  });
}

function filterCat(cat, btn) {
  document.querySelectorAll(".cat-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  document.querySelectorAll(".voice-card").forEach(card => {
    card.classList.toggle("hidden", cat !== "all" && card.dataset.cat !== cat);
  });
}

// ===== Studio steps =====
function goToStep(step) {
  currentStep = step;
  document.querySelectorAll(".studio-panel").forEach((p, i) => {
    p.classList.toggle("active", i + 1 === step);
  });
  // Update step indicators
  document.querySelectorAll(".step").forEach((s, i) => {
    s.classList.remove("active", "done");
    if (i + 1 === step) s.classList.add("active");
    else if (i + 1 < step) s.classList.add("done");
  });
  if (step === 3) updateSummary();
  window.scrollTo({ top: document.getElementById("studio").offsetTop - 80, behavior: "smooth" });
}

function goToPanel(n) {
  // switch upload tab to file tab
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
  document.querySelector('.tab-btn[data-tab="file"]').classList.add("active");
  document.getElementById("tab-file").classList.add("active");
}

function updateSummary() {
  document.getElementById("summaryFile").textContent = selectedFile ? selectedFile.name : "–";
  document.getElementById("summaryVoice").textContent = selectedVoice ? `${selectedVoice.emoji} ${selectedVoice.name}` : "–";
  document.getElementById("summaryPitch").textContent = document.getElementById("pitchSlider")?.value ?? 0;
  const fmt = document.getElementById("outputFormat");
  document.getElementById("summaryFormat").textContent = fmt ? fmt.options[fmt.selectedIndex].text : "MP3";
}

// ===== Generation =====
function startGeneration() {
  if (!selectedFile || !selectedVoice) {
    showToast("⚠️ Thiếu file hoặc chưa chọn giọng!");
    return;
  }

  document.getElementById("generateArea").style.display = "none";
  document.getElementById("step3-back").style.display = "none";
  document.getElementById("progressArea").style.display = "block";
  document.getElementById("resultArea").style.display = "none";

  simulateProcessing();
}

const STAGES = ["stage-upload","stage-separate","stage-convert","stage-merge","stage-export"];
const STAGE_MSGS = [
  "Đang upload file lên server…",
  "Tách vocal và nhạc nền bằng Demucs…",
  `AI đang học giọng hát của bạn…`,
  "Ghép vocal đã chuyển với nhạc nền…",
  "Xuất file và nén âm thanh…",
];
const STAGE_DURATIONS = [800, 1800, 2500, 1200, 800]; // ms per stage (demo)

function simulateProcessing() {
  let progress = 0;
  const bar = document.getElementById("mainProgressBar");
  const msg = document.getElementById("progressMsg");

  STAGES.forEach(id => {
    document.getElementById(id).classList.remove("active","done");
    document.getElementById(id).querySelector(".stage-status").textContent = "";
  });

  function runStage(idx) {
    if (idx >= STAGES.length) {
      bar.style.width = "100%";
      msg.textContent = "✅ Hoàn thành!";
      setTimeout(showResult, 600);
      return;
    }
    const el = document.getElementById(STAGES[idx]);
    el.classList.add("active");
    el.querySelector(".stage-status").textContent = "đang xử lý…";
    msg.textContent = STAGE_MSGS[idx];

    const target = Math.round((100 / STAGES.length) * (idx + 1));
    const step = (target - progress) / (STAGE_DURATIONS[idx] / 50);

    const interval = setInterval(() => {
      progress = Math.min(progress + step, target);
      bar.style.width = progress + "%";
      if (progress >= target) {
        clearInterval(interval);
        el.classList.remove("active");
        el.classList.add("done");
        el.querySelector(".stage-status").textContent = "";
        setTimeout(() => runStage(idx + 1), 200);
      }
    }, 50);
  }

  runStage(0);
}

function showResult() {
  document.getElementById("progressArea").style.display = "none";
  document.getElementById("resultArea").style.display = "block";

  // In a real app, the server returns a URL to the processed file.
  // For demo, reuse the original file as the "result".
  const url = selectedFile ? URL.createObjectURL(selectedFile) : "";
  document.getElementById("resultAudio").src = url;
  document.getElementById("compareOriginal").src = url;
  document.getElementById("compareResult").src = url;
  simulatedResultBlob = selectedFile;

  showToast("🎉 Cover của bạn đã sẵn sàng!");
}

function downloadResult() {
  if (!simulatedResultBlob) return;
  const fmt = document.getElementById("outputFormat")?.value ?? "mp3";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(simulatedResultBlob);
  const voiceName = selectedVoice ? selectedVoice.name.replace(/\s+/g, "_") : "cover";
  a.download = `ai_cover_${voiceName}.${fmt}`;
  a.click();
  showToast("📥 Đang tải xuống file cover…");
}

function shareResult() {
  if (navigator.share) {
    navigator.share({ title: "AI Cover Music", text: `Nghe bản cover AI của tôi – ${selectedVoice?.name}!`, url: window.location.href });
  } else {
    navigator.clipboard.writeText(window.location.href).then(() => showToast("🔗 Đã copy link!"));
  }
}

function resetStudio() {
  selectedFile  = null;
  selectedVoice = null;
  simulatedResultBlob = null;

  // Reset file input
  document.getElementById("audioFileInput").value = "";
  document.getElementById("filePreview").style.display = "none";
  document.getElementById("btn-step1-next").disabled = true;

  // Reset voice
  document.querySelectorAll(".voice-card").forEach(c => c.classList.remove("selected"));
  document.getElementById("btn-step2-next").disabled = true;

  // Reset step 3 UI
  document.getElementById("generateArea").style.display = "flex";
  document.getElementById("step3-back").style.display = "flex";
  document.getElementById("progressArea").style.display = "none";
  document.getElementById("resultArea").style.display = "none";
  document.getElementById("mainProgressBar").style.width = "0%";

  goToStep(1);
  showToast("🔄 Studio đã được reset. Tạo cover mới thôi!");
}

// ===== FAQ =====
function toggleFaq(btn) {
  const item = btn.closest(".faq-item");
  const isOpen = item.classList.contains("open");
  document.querySelectorAll(".faq-item").forEach(i => i.classList.remove("open"));
  if (!isOpen) item.classList.add("open");
}

// ===== Toast =====
let toastTimer = null;
function showToast(msg, duration = 3000) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), duration);
}

// ===== Helpers =====
function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(2) + " MB";
}
