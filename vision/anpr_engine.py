"""
License Plate Recognition & Parsing Engine for Republic of Belarus Standards.
Includes regex validators, Cyrillic-to-Latin homoglyph mapping, positional fuzzy correction,
and EasyOCR image extraction pipeline with heuristic fallback.
"""
import re
import logging
from typing import Optional, Tuple, List
import numpy as np
import cv2

logger = logging.getLogger("smartvision.anpr")

# Republic of Belarus Plate Regex Standards
REGEX_PATTERNS = {
    "CIVILIAN": re.compile(r"^([0-9]{4})\s?([A-Z]{2})-([1-7])$"),          # e.g., 7777 AB-7
    "EV_STANDARD": re.compile(r"^E([0-9]{3})\s?([A-Z]{2})$"),              # e.g., E123 AB
    "EV_REGIONAL": re.compile(r"^E\s?([0-9]{4})-([1-7])$"),                # e.g., E 7777-7
    "TAXI": re.compile(r"^([1-7])\s?TAX\s?([0-9]{4})$"),                  # e.g., 7 TAX 1234
    "GOVERNMENT": re.compile(r"^([0-9]{4})\s?([A-Z]{2})$"),               # e.g., 0001 MI
}

# Cyrillic to Latin visual homoglyphs
CYRILLIC_TO_LATIN = {
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H',
    'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Х': 'X',
    'I': 'I', 'І': 'I'
}

# Character disambiguation maps based on positional expectations
CHAR_TO_DIGIT = {
    'O': '0', 'Q': '0', 'D': '0',
    'I': '1', 'L': '1', 'l': '1', '|': '1', 'J': '1',
    'Z': '2',
    'E': '3',
    'A': '4',
    'S': '5',
    'G': '6', 'b': '6',
    'T': '7',
    'B': '8',
    'g': '9', 'q': '9'
}

DIGIT_TO_CHAR = {
    '0': 'O',
    '1': 'I',
    '2': 'Z',
    '3': 'E',
    '4': 'A',
    '5': 'S',
    '6': 'G',
    '7': 'T',
    '8': 'B',
    '9': 'P'
}


class ANPREngine:
    def __init__(self, use_gpu: bool = False, load_ocr: bool = True):
        self.reader = None
        if load_ocr:
            self._init_ocr(use_gpu)

    def _init_ocr(self, use_gpu: bool) -> None:
        """Initialize EasyOCR only if local weights exist, preventing network hang."""
        try:
            from pathlib import Path
            home_model_dir = Path.home() / ".EasyOCR" / "model"
            craft_path = home_model_dir / "craft_mlt_25k.pth"
            rec_path = home_model_dir / "english_g2.pth"

            if craft_path.exists() and rec_path.exists():
                import easyocr
                self.reader = easyocr.Reader(['en'], gpu=use_gpu, download_enabled=False, verbose=False)
                logger.info("EasyOCR initialized from local cache.")
            else:
                logger.info("EasyOCR weights not present in local cache. Running in fast OpenCV heuristic mode.")
                self.reader = None
        except Exception as e:
            logger.info(f"EasyOCR reader skipped ({e}). Operating in fast OpenCV heuristic fallback.")
            self.reader = None

    @staticmethod
    def normalize_text(raw_text: str) -> str:
        """Strip invalid characters, upper-case, map Cyrillic homoglyphs."""
        if not raw_text:
            return ""
        text = raw_text.upper().strip()
        # Map Cyrillic
        for cyr, lat in CYRILLIC_TO_LATIN.items():
            text = text.replace(cyr, lat)
        # Keep alphanumeric, dashes, spaces
        text = re.sub(r'[^A-Z0-9\-\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @classmethod
    def fuzzy_correct_belarus_civilian(cls, text: str) -> Optional[str]:
        """
        Attempt positional correction for standard civilian plate: 4 digits + 2 letters + '-' + region digit (1-7).
        Example: "7777AB7" -> "7777 AB-7", "O123AB-7" -> "0123 AB-7"
        """
        cleaned = re.sub(r'[\s\-]', '', text)
        if len(cleaned) != 7:
            return None

        d1 = [CHAR_TO_DIGIT.get(c, c) for c in cleaned[0:4]]
        l1 = [DIGIT_TO_CHAR.get(c, c) for c in cleaned[4:6]]
        r1 = CHAR_TO_DIGIT.get(cleaned[6], cleaned[6])

        digits_part = "".join(d1)
        letters_part = "".join(l1)
        region_part = r1

        if (
            digits_part.isdigit()
            and letters_part.isalpha()
            and region_part.isdigit()
            and (1 <= int(region_part) <= 7)
        ):
            return f"{digits_part} {letters_part}-{region_part}"

        return None

    @classmethod
    def validate_plate(cls, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate and format license plate string according to Belarusian standards.
        Returns: (is_valid, formatted_plate, plate_type)
        """
        norm = cls.normalize_text(text)
        if not norm:
            return False, None, None

        # 1. Direct Regex match
        for ptype, pattern in REGEX_PATTERNS.items():
            match = pattern.match(norm)
            if match:
                if ptype == "CIVILIAN":
                    formatted = f"{match.group(1)} {match.group(2)}-{match.group(3)}"
                elif ptype == "EV_STANDARD":
                    formatted = f"E{match.group(1)} {match.group(2)}"
                elif ptype == "EV_REGIONAL":
                    formatted = f"E {match.group(1)}-{match.group(2)}"
                elif ptype == "TAXI":
                    formatted = f"{match.group(1)} TAX {match.group(2)}"
                else:
                    formatted = norm
                return True, formatted, ptype

        # 2. Fuzzy positional correction for standard plates
        corrected = cls.fuzzy_correct_belarus_civilian(norm)
        if corrected:
            return True, corrected, "CIVILIAN"

        return False, None, None

    def preprocess_plate_image(self, plate_crop: np.ndarray) -> np.ndarray:
        """Enhance contrast and binarize plate region for robust OCR."""
        if plate_crop is None or plate_crop.size == 0:
            return plate_crop

        # Resize to standard height for OCR
        h, w = plate_crop.shape[:2]
        if h < 40 or w < 120:
            scale = max(40.0 / max(h, 1), 120.0 / max(w, 1))
            plate_crop = cv2.resize(plate_crop, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        if len(plate_crop.shape) == 3:
            gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = plate_crop

        # Contrast Limited Adaptive Histogram Equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Bilateral filter to smooth noise while preserving edges
        denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)

        # Otsu thresholding
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def read_plate(self, plate_crop: np.ndarray) -> Tuple[Optional[str], float, Optional[str]]:
        """
        Run OCR on plate crop image.
        Returns: (plate_number, confidence, plate_type)
        """
        if plate_crop is None or plate_crop.size == 0:
            return None, 0.0, None

        if self.reader is not None:
            try:
                preprocessed = self.preprocess_plate_image(plate_crop)
                results = self.reader.readtext(preprocessed)
                if not results:
                    results = self.reader.readtext(plate_crop)

                for bbox, text, conf in results:
                    is_valid, formatted, ptype = self.validate_plate(text)
                    if is_valid and formatted:
                        return formatted, float(conf), ptype

                    # Try combined text if multiple tokens detected
                    combined = " ".join([r[1] for r in results])
                    is_valid, formatted, ptype = self.validate_plate(combined)
                    if is_valid and formatted:
                        avg_conf = sum(r[2] for r in results) / len(results)
                        return formatted, float(avg_conf), ptype
            except Exception as e:
                logger.error(f"OCR inference error: {e}")

        return None, 0.0, None

    def find_plate_roi(self, car_crop: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Heuristic locator for rectangular license plate regions within a vehicle crop.
        Returns list of (x, y, w, h) bounding boxes.
        """
        if car_crop is None or car_crop.size == 0:
            return []

        gray = cv2.cvtColor(car_crop, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        sobelx = cv2.Sobel(blur, cv2.CV_8U, 1, 0, ksize=3)
        _, thresh = cv2.threshold(sobelx, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological close to join character contours
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []

        car_h, car_w = car_crop.shape[:2]

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / float(max(h, 1))
            area = w * h
            # Belarus plate aspect ratio ≈ 4.5 to 5.5, area within 0.5% - 15% of car crop
            if 2.5 <= aspect_ratio <= 6.5 and (0.005 * car_w * car_h) < area < (0.20 * car_w * car_h):
                candidates.append((x, y, w, h))

        return candidates
