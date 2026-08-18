import cv2
import threading
import time
import easyocr
import numpy as np
import requests
from ultralytics import YOLO
from PIL import ImageFont, ImageDraw, Image
from collections import Counter
import re

# ─── Configuration ────────────────────────────────────────────────────────────
MODEL_PATH        = "D:\\graduation_project\\best.pt"
CAMERA_SOURCE     = 1                    # local camera index OR "http://IP:8080/video"
ESP32_IP          = "10.188.134.241"
BACKEND_URL       = "http://localhost:8000"
PARKING_ID        = "parking_2"
DEVICE_KEY        = "esp32_parking2_key"
GATE_NAME         = "Gate A"
TOTAL_SPOTS       = 3
COOLDOWN_SEC      = 10
SLOTS_REFRESH_SEC = 5

# ─── OCR Configuration ────────────────────────────────────────────────────────
CONF_THRESHOLD   = 0.25
OCR_LANGUAGES    = ['ar', 'en']
VOTE_BUFFER_SIZE = 7        # larger window → more stable majority
MIN_VOTES        = 3        # need 3/7 agreement
OCR_CONF_MIN     = 0.20     # minimum per-box OCR confidence

# ─── Shared State ─────────────────────────────────────────────────────────────
readings_buffer  = []
confirmed_result = None
no_plate_frames  = 0
current_frame    = None
latest_data = {
    "box":          None,
    "status":       "Waiting",
    "arabic_text":  "",
    "english_text": "",
    "gate_label":   "",
    "gate_color":   (255, 255, 255)
}
lock             = threading.Lock()
is_running       = True
last_open_time   = 0
last_slots_check = 0
cached_slots     = -1

# ─── OCR Helpers ─────────────────────────────────────────────────────────────

def is_arabic_text(text: str) -> bool:
    return bool(re.search(r'[؀-ۿ]', text))


def smart_fix_block(text: str) -> str:
    """
    Fix common misreads:
      • pure-digit context  B→8, O→0, I/l→1, S→5, Z→2
      • alphanumeric context  8→B, 0→O
    """
    has_alpha  = bool(re.search(r'[a-zA-Z؀-ۿ]', text))
    has_digit  = bool(re.search(r'\d', text))
    pure_digit = not has_alpha and has_digit

    if pure_digit:
        text = re.sub(r'[Bb]', '8', text)
        text = re.sub(r'[Oo]', '0', text)
        text = re.sub(r'[IiLl]', '1', text)
        text = re.sub(r'[Ss]', '5', text)
        text = re.sub(r'[Zz]', '2', text)
    elif has_alpha and has_digit:
        text = text.replace('8', 'B').replace('0', 'O')

    return text


def preprocess_plate(img: np.ndarray):
    """Return (colour_upscale, sharpened_threshold) for dual-pass OCR."""
    big      = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    colour   = big.copy()
    gray     = cv2.cvtColor(big, cv2.COLOR_BGR2GRAY)
    kernel   = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    _, thresh = cv2.threshold(sharpened, 0, 255, cv2.THRESH_OTSU)
    return colour, thresh


def get_most_common(readings_list: list):
    if not readings_list:
        return None
    data = Counter(readings_list)
    most_common, count = data.most_common(1)[0]
    if count >= MIN_VOTES:
        return most_common
    return None


def parse_ocr_results(ocr_results) -> tuple:
    """
    Spatially sort OCR boxes left-to-right, split into Arabic vs Latin/digit
    tokens, reverse Arabic tokens for RTL display, and format with spaced chars.
    """
    ocr_results.sort(key=lambda r: r[0][0][0])

    ar_tokens = []
    en_tokens = []

    for (bbox, raw_text, conf) in ocr_results:
        if conf < OCR_CONF_MIN:
            continue
        clean = re.sub(r'[.\-_\s]+', ' ', raw_text).strip()
        if not clean:
            continue
        clean  = smart_fix_block(clean)
        left_x = bbox[0][0]
        if is_arabic_text(clean):
            ar_tokens.append((left_x, clean))
        else:
            en_tokens.append((left_x, clean))

    ar_tokens.sort(key=lambda t: t[0])
    final_ar = spaced_chars([t[1] for t in reversed(ar_tokens)])

    en_tokens.sort(key=lambda t: t[0])
    final_en = spaced_chars([t[1] for t in en_tokens])

    return final_ar, final_en


def spaced_chars(tokens: list) -> str:
    """Join tokens with double-space; put single spaces between each character."""
    if not tokens:
        return ""
    return "  ".join(" ".join(list(tok)) for tok in tokens)


def run_ocr_on(reader, img_variants: list) -> list:
    """Try OCR on multiple image variants; return the highest-confidence result set."""
    best_results = []
    best_score   = -1.0
    for img in img_variants:
        try:
            results = reader.readtext(img)
            score   = sum(c for (_, _, c) in results) / max(len(results), 1)
            if score > best_score:
                best_score   = score
                best_results = results
        except Exception:
            pass
    return best_results


# ─── Backend Helpers ──────────────────────────────────────────────────────────

def check_plate(plate: str, confidence: float) -> bool:
    """POST /api/v1/iot/plate-detect — True if plate has an active booking."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/v1/iot/plate-detect",
            params={
                "parking_id": PARKING_ID,
                "plate":      plate,
                "action":     "entry",
                "gate":       GATE_NAME,
                "confidence": round(confidence, 2),
                "device_key": DEVICE_KEY,
            },
            timeout=5
        )
        print(f"  [plate-detect] {resp.status_code} → {resp.text[:100]}")
        return resp.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"  [BACKEND ERROR] {e}")
        return False


def get_available_spots() -> int:
    """GET /api/v1/parkings/{id}/slots/available — count or -1 if offline."""
    try:
        resp = requests.get(
            f"{BACKEND_URL}/api/v1/parkings/{PARKING_ID}/slots/available",
            timeout=5
        )
        if resp.status_code == 200:
            return len(resp.json())
        return 0
    except requests.exceptions.RequestException as e:
        print(f"  [BACKEND OFFLINE] {e}")
        return -1


def open_gate(new_visitor: bool = False) -> bool:
    """Send /open (green) or /open_new (yellow) to ESP32."""
    endpoint = "/open_new" if new_visitor else "/open"
    try:
        resp = requests.get(f"http://{ESP32_IP}{endpoint}", timeout=5)
        print(f"  ESP32 → {resp.text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  [ESP32 ERROR] {e}")
        return False


# ─── Gate Decision Logic ──────────────────────────────────────────────────────

def handle_confirmed_plate(ar_text, en_text, yolo_conf):
    global last_open_time, cached_slots

    now = time.time()
    if now - last_open_time < COOLDOWN_SEC:
        remaining = COOLDOWN_SEC - (now - last_open_time)
        print(f"  Cooldown — {remaining:.1f}s remaining, skipping")
        return None, None

    plate_text = en_text.replace(" ", "").upper() if en_text else ar_text.replace(" ", "")
    print(f"\n  Gate check → AR[{ar_text}]  EN[{en_text}]")

    authorized = check_plate(plate_text, yolo_conf)

    if authorized:
        print("  AUTHORIZED (active booking) → green LED")
        label, color = "AUTHORIZED", (0, 255, 0)
        if open_gate(new_visitor=False):
            last_open_time = now
            if cached_slots > 0:
                cached_slots -= 1

    elif cached_slots == -1:
        print("  BACKEND OFFLINE")
        label, color = "BACKEND OFFLINE", (0, 165, 255)

    elif cached_slots > 0:
        print(f"  No booking — {cached_slots} spot(s) free → yellow LED")
        label, color = f"NEW ENTRY  ({cached_slots} spots left)", (0, 200, 255)
        if open_gate(new_visitor=True):
            last_open_time = now
            cached_slots  -= 1

    else:
        print("  DENIED — parking full → red LED")
        label, color = "PARKING FULL", (0, 0, 255)

    return label, color


# ─── PIL Overlay ──────────────────────────────────────────────────────────────

def draw_overlay(img, ar_text, en_text, gate_label, gate_color, position, box_w, status):
    try:
        x, y    = position
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw    = ImageDraw.Draw(img_pil)

        try:
            font_ar   = ImageFont.truetype("arial.ttf", 40)
            font_en   = ImageFont.truetype("arial.ttf", 35)
            font_gate = ImageFont.truetype("arial.ttf", 28)
        except Exception:
            font_ar = font_en = font_gate = ImageFont.load_default()

        lines     = sum([bool(ar_text), bool(en_text), bool(gate_label)])
        bg_height = max(50, lines * 42 + 16)
        panel_w   = max(box_w, 260)

        draw.rectangle([(x, y - bg_height), (x + panel_w, y)], fill=(0, 0, 0))

        if status == "Scanning":
            draw.text((x + 10, y - 38), "Scanning...", font=font_en, fill=(255, 200, 0))
        else:
            cy = y - bg_height + 6
            if ar_text:
                draw.text((x + 10, cy), ar_text,    font=font_ar,   fill=(255, 255, 255)); cy += 44
            if en_text:
                draw.text((x + 10, cy), en_text,    font=font_en,   fill=(0, 255, 255));  cy += 40
            if gate_label:
                draw.text((x + 10, cy), gate_label, font=font_gate, fill=gate_color)
            draw.text((x + panel_w - 42, y - 48), "OK", font=font_en, fill=(0, 255, 0))

        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"  [OVERLAY ERROR] {e}")
        return img


# ─── AI Worker Thread ─────────────────────────────────────────────────────────

def ai_worker():
    global current_frame, latest_data, is_running
    global readings_buffer, confirmed_result, no_plate_frames

    print("[AI] Engine starting ...")
    try:
        detector = YOLO(MODEL_PATH)
        reader   = easyocr.Reader(OCR_LANGUAGES, gpu=False)
        print("[AI] Engine ready!\n")
    except Exception as e:
        print(f"[MODEL ERROR] {e}")
        return

    while is_running:
        with lock:
            if current_frame is None:
                time.sleep(0.01)
                continue
            frame_to_process = current_frame.copy()

        detect_frame = cv2.resize(frame_to_process, (640, 480))
        results      = detector.predict(detect_frame, conf=CONF_THRESHOLD, verbose=False)
        found_plate  = False

        for result in results:
            if len(result.boxes) == 0:
                continue

            box             = result.boxes[0]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            yolo_conf       = float(box.conf[0])

            with lock:
                latest_data["box"] = (x1, y1, x2, y2)
                if latest_data["status"] != "Confirmed":
                    latest_data["status"] = "Scanning"

            h_img, w_img = detect_frame.shape[:2]
            cx1 = max(0,     x1 - 10)
            cy1 = max(0,     y1 - 10)
            cx2 = min(w_img, x2 + 10)
            cy2 = min(h_img, y2 + 10)
            plate_img   = detect_frame[cy1:cy2, cx1:cx2]
            found_plate = True
            no_plate_frames = 0

            if confirmed_result is not None:
                break  # already locked in, skip OCR until plate leaves

            try:
                colour_img, thresh_img = preprocess_plate(plate_img)
                ocr_results = run_ocr_on(reader, [colour_img, thresh_img])

                if not ocr_results:
                    break

                final_ar, final_en = parse_ocr_results(ocr_results)

                if not final_ar and not final_en:
                    break

                readings_buffer.append((final_ar, final_en))
                print(f"  [OCR] Ar=[{final_ar}]  En=[{final_en}]")

                if len(readings_buffer) >= VOTE_BUFFER_SIZE:
                    winner = get_most_common(readings_buffer)
                    if winner:
                        confirmed_result = winner
                        win_ar, win_en   = winner
                        print(f"  [CONFIRMED] AR[{win_ar}]  EN[{win_en}]")

                        gate_label, gate_color = handle_confirmed_plate(
                            win_ar, win_en, yolo_conf
                        )
                        with lock:
                            latest_data = {
                                "box":          (x1, y1, x2, y2),
                                "status":       "Confirmed",
                                "arabic_text":  win_ar,
                                "english_text": win_en,
                                "gate_label":   gate_label or "",
                                "gate_color":   gate_color or (255, 255, 255)
                            }
                    else:
                        # No clear winner yet — drop oldest half and keep going
                        readings_buffer = readings_buffer[VOTE_BUFFER_SIZE // 2:]

            except Exception as e:
                print(f"  [OCR ERROR] {e}")

            break  # only process highest-confidence box

        if not found_plate:
            no_plate_frames += 1
            if no_plate_frames > 20:
                confirmed_result = None
                readings_buffer  = []
                with lock:
                    latest_data = {
                        "box": None, "status": "Waiting",
                        "arabic_text": "", "english_text": "",
                        "gate_label": "", "gate_color": (255, 255, 255)
                    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def run_system():
    global current_frame, is_running, cached_slots, last_slots_check

    cap = cv2.VideoCapture(CAMERA_SOURCE)
    if isinstance(CAMERA_SOURCE, int):
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("ERROR: Cannot open camera. Check CAMERA_SOURCE.")
        return

    cached_slots     = get_available_spots()
    last_slots_check = time.time()

    thread        = threading.Thread(target=ai_worker)
    thread.daemon = True
    thread.start()

    print("=== Smart Parking Gate Running ===")
    print(f"Backend : {BACKEND_URL}")
    print(f"Parking : {PARKING_ID}")
    print(f"ESP32   : http://{ESP32_IP}")
    print(f"Slots   : {cached_slots}/{TOTAL_SPOTS}")
    print("Press 'q' to quit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame — retrying...")
            time.sleep(0.5)
            continue

        now   = time.time()
        frame = cv2.resize(frame, (640, 480))

        with lock:
            current_frame = frame.copy()
            data          = latest_data.copy()

        # Refresh slot count from backend periodically
        if now - last_slots_check > SLOTS_REFRESH_SEC:
            cached_slots     = get_available_spots()
            last_slots_check = now

        # Draw plate bounding box
        if data["box"] is not None:
            x1, y1, x2, y2 = data["box"]
            box_color = (0, 255, 0) if data["status"] == "Confirmed" else (0, 255, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 3)
            frame = draw_overlay(
                frame,
                data["arabic_text"], data["english_text"],
                data["gate_label"],  data["gate_color"],
                (x1, y1), x2 - x1,  data["status"]
            )

        # HUD: parking spots counter
        if cached_slots == -1:
            hud_color, hud_text = (0, 165, 255), "Parking: BACKEND OFFLINE"
        elif cached_slots > 0:
            hud_color, hud_text = (0, 255, 0),   f"Parking: {cached_slots}/{TOTAL_SPOTS} spots free"
        else:
            hud_color, hud_text = (0, 0, 255),   f"Parking: FULL (0/{TOTAL_SPOTS})"

        cv2.rectangle(frame, (0, 0), (320, 40), (0, 0, 0), -1)
        cv2.putText(frame, hud_text, (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, hud_color, 2)

        cv2.imshow("Smart Parking Gate", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            is_running = False
            break

    cap.release()
    cv2.destroyAllWindows()
    print("System stopped.")


if __name__ == '__main__':
    run_system()
