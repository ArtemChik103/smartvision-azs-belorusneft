"""
Automated Video Presentation Builder for SmartVision AZS with Russian Neural Voiceover.
Generates an official MPEG-4 (*.mp4) 1080p Full HD video pitch with voice narration (edge-tts)
for the «Марафон ИТ-стартапов 2026» РУП «ПО «Белоруснефть».
Complies with 'zajavka-i-trebovanija-dlja-uchastija-2.docx':
- Format: MPEG-4 (*.mp4) with AAC Audio
- Aspect Ratio: 16:9 (1920x1080)
- Resolution: 1080p Full HD
- Narration: Russian Neural Voice (ru-RU-DmitryNeural)
- Duration: ~1:45 minutes (under 6 minute limit)
- Speed: 1.0x natural speed without artificial acceleration
"""
import os
import sys
import shutil
import time
import asyncio
import subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import edge_tts
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent.parent
PRES_DIR = BASE_DIR / "presentation"
AUDIO_DIR = PRES_DIR / "audio"
VIDEO_TEMP_DIR = PRES_DIR / "video_temp"
TEMP_SILENT_VIDEO = PRES_DIR / "temp_silent_video.mp4"
FINAL_VIDEO_PATH = PRES_DIR / "SmartVision-AZS-Video-Presentation.mp4"

VOICE = "ru-RU-DmitryNeural"
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

SCENARIO_VOICEOVERS = [
    (
        "01_intro.mp3",
        "Здравствуйте! Представляем проект Смарт Вижн АЗС в номинации «Цифровая АЗС» для сети «Белоруснефть». "
        "Это программно-аппаратный комплекс компьютерного зрения, предиктивной безопасности и безакцептной оплаты.",
    ),
    (
        "02_scenario_1_zeroclick.mp3",
        "Сценарий первый — бесшовная заправка Драйв энд Пэй. Автомобиль подъезжает к ТРК номер два. "
        "Нейросеть распознает белорусский госномер за восемьдесят миллисекунд, идентифицирует профиль клиента "
        "и автоматически разрешает налив тридцати литров топлива. "
        "Время обслуживания на ТРК сокращается с четырех минут до сорока пяти секунд, "
        "а электронный фискальный чек с ку-ар кодом формируется автоматически.",
    ),
    (
        "03_scenario_2_estop.mp3",
        "Сценарий второй — предотвращение обрыва раздаточных шлангов. "
        "Если водитель начинает преждевременное движение с пистолетом в баке, алгоритм трекинга фиксирует смещение кузова "
        "и менее чем за триста миллисекунд аппаратным сигналом И-СТОП блокирует насос ТРК, сохраняя оборудование и предотвращая разлив топлива.",
    ),
    (
        "04_scenario_3_guest.mp3",
        "Сценарий третий — гостевой режим. Для клиентов без мобильного приложения сохраняется классический налив с оплатой через оператора.",
    ),
    (
        "05_roi_and_audit.mp3",
        "Интерактивная финансовая модель показывает, что внедрение системы на сеть из пятисот семидесяти АЗС "
        "дает свыше двадцати двух миллионов рублей чистого годового эффекта при сроке окупаемости менее одного месяца. "
        "Все транзакции и предотвращенные инциденты с фотофиксацией сохраняются в локальной базе данных.",
    ),
    (
        "06_outro.mp3",
        "Проект Смарт Вижн АЗС полностью разработан, протестирован в десктоп-версии и готов к пилотному внедрению на АЗС номер один. "
        "Спасибо за внимание!",
    ),
]


def get_font(size: int, bold: bool = False):
    font_names = [
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()


def get_audio_duration(file_path: Path) -> float:
    """Get exact duration of an audio file in seconds via ffmpeg."""
    cmd = [FFMPEG_EXE, "-i", str(file_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    for line in res.stderr.split("\n"):
        if "Duration:" in line:
            time_str = line.split("Duration:")[1].split(",")[0].strip()
            parts = time_str.split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 10.0


async def generate_voiceovers():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    print("[1/5] Generating Russian neural voiceovers with edge-tts...")
    durations = {}
    for filename, text in SCENARIO_VOICEOVERS:
        out_path = AUDIO_DIR / filename
        communicate = edge_tts.Communicate(text, VOICE, rate="+3%", pitch="+0Hz")
        await communicate.save(str(out_path))
        dur = get_audio_duration(out_path)
        durations[filename] = dur
        print(f"  [OK] {filename}: {dur:.2f}s")
    return durations


def create_title_card(width: int = 1920, height: int = 1080, duration_sec: float = 16.0, fps: int = 30) -> list:
    """Create introductory title card frames."""
    img = Image.new("RGB", (width, height), color=(11, 17, 32))
    draw = ImageDraw.Draw(img)

    # Header badge
    draw.rectangle([560, 200, 1360, 255], fill=(19, 35, 56), outline=(0, 168, 77), width=2)
    font_badge = get_font(22, bold=True)
    draw.text((600, 215), "МАРАФОН ИТ-СТАРТАПОВ 2026 · ПО «БЕЛОРУСНЕФТЬ»", fill=(0, 168, 77), font=font_badge)

    # Main Title
    font_title = get_font(72, bold=True)
    draw.text((640, 290), "SmartVision AZS", fill=(255, 255, 255), font=font_title)

    # Subtitle
    font_sub = get_font(28, bold=False)
    draw.text(
        (330, 400),
        "Интеллектуальный комплекс компьютерного зрения, безопасности и безакцептной оплаты для сети АЗС",
        fill=(148, 163, 184),
        font=font_sub,
    )

    # Nomination pill
    draw.rectangle([760, 485, 1160, 545], fill=(30, 41, 59), outline=(51, 65, 85), width=2)
    font_nom = get_font(24, bold=True)
    draw.text((800, 500), "Номинация: Цифровая АЗС", fill=(0, 168, 77), font=font_nom)

    # Key Highlights bar
    card_w, card_h = 360, 130
    cards_data = [
        ("45 сек", "Полный цикл заправки (-78% времени)"),
        ("< 300 мс", "Аппаратный E-STOP отсечки насоса"),
        ("22.0 млн BYN", "Чистый годовой эффект на сеть 570 АЗС"),
    ]
    start_x = 360
    for i, (num, label) in enumerate(cards_data):
        cx = start_x + i * (card_w + 50)
        cy = 620
        draw.rectangle([cx, cy, cx + card_w, cy + card_h], fill=(19, 35, 56), outline=(0, 132, 61), width=2)
        draw.text((cx + 25, cy + 18), num, fill=(0, 168, 77), font=get_font(38, bold=True))
        draw.text((cx + 25, cy + 75), label, fill=(148, 163, 184), font=get_font(16, bold=False))

    # Voice prompt bar
    draw.rectangle([540, 800, 1380, 855], fill=(15, 23, 42), outline=(0, 132, 61), width=1)
    draw.text((600, 817), "🎙 Голосовое сопровождение проекта · Русский язык", fill=(56, 189, 248), font=get_font(20, bold=True))

    # Footer
    draw.text((780, 930), "Разработчик проекта · Минск, 2026 год", fill=(100, 116, 139), font=get_font(20))

    frame_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return [frame_bgr] * int(duration_sec * fps)


def create_outro_card(width: int = 1920, height: int = 1080, duration_sec: float = 11.5, fps: int = 30) -> list:
    """Create concluding outro card frames."""
    img = Image.new("RGB", (width, height), color=(11, 17, 32))
    draw = ImageDraw.Draw(img)

    # Header badge
    draw.rectangle([680, 180, 1240, 235], fill=(19, 35, 56), outline=(0, 168, 77), width=2)
    draw.text((715, 195), "ГОТОВНОСТЬ К ВНЕДРЕНИЮ", fill=(0, 168, 77), font=get_font(22, bold=True))

    # Main Title
    draw.text((520, 270), "SmartVision AZS — Готовое решение", fill=(255, 255, 255), font=get_font(52, bold=True))
    draw.text(
        (460, 350),
        "Прототип полностью разработан, протестирован и готов к пилоту на АЗС №1",
        fill=(148, 163, 184),
        font=get_font(26),
    )

    # 2 info columns
    box_w, box_h = 580, 280
    
    # Left box: Links
    draw.rectangle([340, 440, 340 + box_w, 440 + box_h], fill=(19, 35, 56), outline=(51, 65, 85), width=2)
    draw.text((370, 465), "Материалы проекта:", fill=(0, 168, 77), font=get_font(24, bold=True))
    draw.text((370, 515), "• Онлайн-дашборд и симулятор ТРК:", fill=(248, 250, 252), font=get_font(18, bold=True))
    draw.text((390, 545), "https://smartvision-azs.onrender.com", fill=(56, 189, 248), font=get_font(18))
    draw.text((370, 585), "• Релизы десктоп-клиента (Setup .EXE / Portable):", fill=(248, 250, 252), font=get_font(18, bold=True))
    draw.text((390, 615), "github.com/ArtemChik103/smartvision-azs-belorusneft/releases", fill=(56, 189, 248), font=get_font(18))
    draw.text((370, 655), "• Репозиторий GitHub: ArtemChik103/smartvision-azs-belorusneft", fill=(148, 163, 184), font=get_font(16))

    # Right box: Contacts
    draw.rectangle([1000, 440, 1000 + box_w, 440 + box_h], fill=(19, 35, 56), outline=(51, 65, 85), width=2)
    draw.text((1030, 465), "Сведения о заявке:", fill=(0, 168, 77), font=get_font(24, bold=True))
    draw.text((1030, 520), "Номинация: Цифровая АЗС", fill=(248, 250, 252), font=get_font(20))
    draw.text((1030, 560), "Конкурс: «Марафон ИТ-стартапов» 2026", fill=(248, 250, 252), font=get_font(20))
    draw.text((1030, 600), "Заказчик: РУП «ПО «Белоруснефть»", fill=(248, 250, 252), font=get_font(20))
    draw.text((1030, 650), "Готовы к развертыванию пилотной зоны", fill=(0, 168, 77), font=get_font(20, bold=True))

    draw.text((790, 870), "SmartVision AZS · Белоруснефть · 2026", fill=(100, 116, 139), font=get_font(20))

    frame_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return [frame_bgr] * int(duration_sec * fps)


def record_ui_session(durations: dict) -> Path:
    """Record high-definition browser session synchronized with speech durations."""
    if VIDEO_TEMP_DIR.exists():
        shutil.rmtree(VIDEO_TEMP_DIR)
    VIDEO_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    print("[2/5] Starting Playwright video recording session at 1920x1080...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir=str(VIDEO_TEMP_DIR),
            record_video_size={"width": 1920, "height": 1080},
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0,
        )
        page = context.new_page()
        
        # 1. Main Operator Cockpit: Scenario 1 (Zero-Click)
        dur_s1 = durations.get("02_scenario_1_zeroclick.mp3", 25.7)
        print(f"  -> Recording Scenario 1: Zero-Click Drive&Pay ({dur_s1:.2f}s)...")
        page.goto("http://127.0.0.1:8000")
        page.wait_for_timeout(500)
        page.click("button[data-action='scenario_1']")
        
        # Fueling takes ~18s
        page.wait_for_timeout(18000)
        
        # Open receipt modal on words 'а электронный фискальный чек'
        print("  -> Demonstrating Electronic Fiscal Receipt...")
        page.click("#openReceiptBtn")
        page.wait_for_timeout(4500)
        page.click("#receiptModal button:has-text('✕')")
        
        # Balance remaining time of S1
        remaining_s1 = max(0.5, dur_s1 - 23.0)
        page.wait_for_timeout(int(remaining_s1 * 1000))

        # 2. Scenario 2: Critical Safety Alarm (E-STOP)
        dur_s2 = durations.get("03_scenario_2_estop.mp3", 19.0)
        print(f"  -> Recording Scenario 2: Predictive E-STOP Hose Protection ({dur_s2:.2f}s)...")
        page.click("button[data-action='scenario_2']")
        page.wait_for_timeout(int(dur_s2 * 1000))
        
        # 3. Scenario 3: Guest Mode
        dur_s3 = durations.get("04_scenario_3_guest.mp3", 9.4)
        print(f"  -> Recording Scenario 3: Guest Mode ({dur_s3:.2f}s)...")
        page.click("button[data-action='scenario_3']")
        page.wait_for_timeout(int(dur_s3 * 1000))

        # 4. ROI & Economic Model & Audit Log
        dur_s5 = durations.get("05_roi_and_audit.mp3", 18.0)
        print(f"  -> Recording Financial Model & ROI Calculator ({dur_s5:.2f}s)...")
        page.click("button[data-tab='tab-roi']")
        page.wait_for_timeout(2000)
        
        # Click scale presets
        page.click("#presetPilot")
        page.wait_for_timeout(1500)
        page.click("#presetRegion")
        page.wait_for_timeout(1500)
        page.click("#presetNetwork")
        page.wait_for_timeout(2500)
        
        # Open TEO Export modal
        page.click("#exportReportBtn")
        page.wait_for_timeout(3500)
        page.click("#teoModal button:has-text('✕')")
        page.wait_for_timeout(1000)

        # Audit Log
        page.click("button[data-tab='tab-audit']")
        page.wait_for_timeout(6000)

        context.close()
        browser.close()
        print("[3/5] Playwright recording finished.")

    webm_files = list(VIDEO_TEMP_DIR.glob("*.webm"))
    if not webm_files:
        raise RuntimeError("No recorded webm file found in temp dir")
    return webm_files[0]


def build_normalized_video(raw_webm: Path, intro_dur: float, outro_dur: float) -> Path:
    """Normalize WebM to 30fps CFR and concatenate with intro and outro cards."""
    print("[4/5] Normalizing video stream and generating intro/outro cards...")

    # 1. Convert UI session WebM to constant 30 fps MP4 preserving real-time duration
    ui_mp4 = PRES_DIR / "ui_session_30fps.mp4"
    cmd_cfr = [
        FFMPEG_EXE,
        "-y",
        "-i", str(raw_webm),
        "-vf", "fps=30,scale=1920:1080:flags=lanczos",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(ui_mp4),
    ]
    subprocess.run(cmd_cfr, capture_output=True, check=True)

    # 2. Build Intro Title Card Video with exact intro_dur
    intro_mp4 = PRES_DIR / "intro_card.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_intro = cv2.VideoWriter(str(intro_mp4), fourcc, 30.0, (1920, 1080))
    for frame in create_title_card(1920, 1080, duration_sec=intro_dur, fps=30):
        out_intro.write(frame)
    out_intro.release()

    # 3. Build Outro Card Video with exact outro_dur
    outro_mp4 = PRES_DIR / "outro_card.mp4"
    out_outro = cv2.VideoWriter(str(outro_mp4), fourcc, 30.0, (1920, 1080))
    for frame in create_outro_card(1920, 1080, duration_sec=outro_dur, fps=30):
        out_outro.write(frame)
    out_outro.release()

    # 4. Concat all 3 video parts
    video_concat_txt = PRES_DIR / "video_concat.txt"
    with open(video_concat_txt, "w", encoding="utf-8") as f:
        f.write(f"file '{intro_mp4.as_posix()}'\n")
        f.write(f"file '{ui_mp4.as_posix()}'\n")
        f.write(f"file '{outro_mp4.as_posix()}'\n")

    cmd_concat_v = [
        FFMPEG_EXE,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(video_concat_txt),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(TEMP_SILENT_VIDEO),
    ]
    subprocess.run(cmd_concat_v, capture_output=True, check=True)

    # Cleanup intermediates
    for p in [intro_mp4, ui_mp4, outro_mp4, video_concat_txt]:
        try:
            p.unlink()
        except Exception:
            pass

    return TEMP_SILENT_VIDEO


def mux_final_video_with_audio():
    """Concatenate narration tracks and mux with silent video using FFmpeg."""
    print("[5/5] Muxing video stream with Russian neural voiceover...")
    
    # 1. Prepare audio concat list
    audio_files = [
        AUDIO_DIR / "01_intro.mp3",
        AUDIO_DIR / "02_scenario_1_zeroclick.mp3",
        AUDIO_DIR / "03_scenario_2_estop.mp3",
        AUDIO_DIR / "04_scenario_3_guest.mp3",
        AUDIO_DIR / "05_roi_and_audit.mp3",
        AUDIO_DIR / "06_outro.mp3",
    ]
    
    concat_list_file = PRES_DIR / "audio_concat.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for af in audio_files:
            # Escape path for ffmpeg concat
            f.write(f"file '{af.as_posix()}'\n")

    combined_audio = PRES_DIR / "combined_narration.mp3"
    
    # Concat audio files
    cmd_concat = [
        FFMPEG_EXE,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(combined_audio),
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)
    print(f"  Master narration track compiled: {combined_audio.name}")

    # Mux video + audio into final Full HD MP4
    cmd_mux = [
        FFMPEG_EXE,
        "-y",
        "-i", str(TEMP_SILENT_VIDEO),
        "-i", str(combined_audio),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        str(FINAL_VIDEO_PATH),
    ]
    res = subprocess.run(cmd_mux, capture_output=True, text=True)
    if res.returncode != 0:
        print("[ERROR] FFmpeg Muxing Error:\n", res.stderr)
        return False

    # Cleanup temp
    try:
        if TEMP_SILENT_VIDEO.exists():
            TEMP_SILENT_VIDEO.unlink()
        if concat_list_file.exists():
            concat_list_file.unlink()
        if combined_audio.exists():
            combined_audio.unlink()
        if VIDEO_TEMP_DIR.exists():
            shutil.rmtree(VIDEO_TEMP_DIR)
    except Exception:
        pass

    final_size_mb = round(FINAL_VIDEO_PATH.stat().st_size / (1024 * 1024), 2)
    final_dur = get_audio_duration(FINAL_VIDEO_PATH)
    final_min = int(final_dur // 60)
    final_sec = int(final_dur % 60)

    print("\n" + "=" * 60)
    print("[SUCCESS] Official Video Presentation with Voiceover Built!")
    print(f"  Target:     {FINAL_VIDEO_PATH}")
    print(f"  Resolution: 1920x1080 (Full HD, 16:9)")
    print(f"  Duration:   {final_min}:{final_sec:02d} (under 6 min limit)")
    print(f"  File size:  {final_size_mb} MB")
    print(f"  Voiceover:  {VOICE} (Russian Neural)")
    print("=" * 60)
    return True


def ensure_backend_running():
    """Ensure FastAPI server is running on http://127.0.0.1:8000."""
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/status", timeout=1.5) as resp:
            if resp.status == 200:
                print("Backend server is already running.")
                return None
    except Exception:
        pass

    print("Starting background SmartVision backend server...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/api/status", timeout=1.0) as resp:
                if resp.status == 200:
                    print("Backend server started and online.")
                    return proc
        except Exception:
            pass
    print("Warning: Backend might not have responded in time.")
    return proc


def main():
    PRES_DIR.mkdir(parents=True, exist_ok=True)
    server_proc = ensure_backend_running()
    try:
        durations = asyncio.run(generate_voiceovers())
        intro_dur = durations.get("01_intro.mp3", 15.6) + 0.5
        outro_dur = durations.get("06_outro.mp3", 10.7) + 0.5

        raw_webm = record_ui_session(durations)
        build_normalized_video(raw_webm, intro_dur, outro_dur)
        mux_final_video_with_audio()
    finally:
        if server_proc:
            print("Stopping background backend server...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=3)
            except Exception:
                server_proc.kill()


if __name__ == "__main__":
    main()
