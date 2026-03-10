import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import cv2
import easyocr
from ultralytics import YOLO
from datetime import datetime
import os
import re
import difflib
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, PatternFill, Alignment

# --- 1. CONFIGURATION ---
INPUT_FOLDER = "test_images"       
OUTPUT_FOLDER = "test_results"     
LOG_FILE = "batch_log.xlsx"
DEVICE = 'cpu'

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
evidence_folder = os.path.join(OUTPUT_FOLDER, "evidence_plates")
os.makedirs(evidence_folder, exist_ok=True)

NIGERIA_STATES = {
    "ABJ": "Abuja", "FCT": "Abuja", "ABUJA": "Abuja", "ABIA": "Abia", "ADAMAWA": "Adamawa", 
    "AKWA": "Akwa Ibom", "IBOM": "Akwa Ibom", "ANAMBRA": "Anambra", "BAUCHI": "Bauchi", 
    "BAYELSA": "Bayelsa", "BENUE": "Benue", "BORNO": "Borno", "CROSS": "Cross River", 
    "DELTA": "Delta", "EBONYI": "Ebonyi", "EDO": "Edo", "EKITI": "Ekiti", "ENUGU": "Enugu", 
    "GOMBE": "Gombe", "IMO": "Imo", "JIGAWA": "Jigawa", "KADUNA": "Kaduna", "KANO": "Kano", 
    "KATSINA": "Katsina", "KEBBI": "Kebbi", "KOGI": "Kogi", "KWARA": "Kwara", "LAGOS": "Lagos", 
    "CENTRE": "Lagos", "EXCELLENCE": "Lagos", "NASARAWA": "Nasarawa", "NIGER": "Niger", 
    "OGUN": "Ogun", "ONDO": "Ondo", "OSUN": "Osun", "OYO": "Oyo", "PLATEAU": "Plateau", 
    "RIVERS": "Rivers", "SOKOTO": "Sokoto", "TARABA": "Taraba", "YOBE": "Yobe", "ZAMFARA": "Zamfara"
}

# --- ULTIMATE 36-STATE LGA PREFIX MAP ---
LGA_MAP = {
    "ABA": "Abia", "BND": "Abia", "ACH": "Abia", "HAF": "Abia", "UMA": "Abia", "KPU": "Abia",
    "DSA": "Adamawa", "FUR": "Adamawa", "GAN": "Adamawa", "GRE": "Adamawa", "GMB": "Adamawa", "GUY": "Adamawa", "HNG": "Adamawa", "JMT": "Adamawa", "MUB": "Adamawa", "NUM": "Adamawa", "YLA": "Adamawa",
    "ABK": "Akwa Ibom", "KRT": "Akwa Ibom", "KET": "Akwa Ibom", "KST": "Akwa Ibom", "AFH": "Akwa Ibom", "AEE": "Akwa Ibom", "ETN": "Akwa Ibom", "UYO": "Akwa Ibom",
    "AGU": "Anambra", "ABN": "Anambra", "ACA": "Anambra", "AJL": "Anambra", "HAL": "Anambra", "HTE": "Anambra", "AWK": "Anambra", "NNE": "Anambra", "ONN": "Anambra",
    "BAU": "Bauchi", "BLR": "Bauchi", "BTA": "Bauchi", "DAS": "Bauchi", "DKU": "Bauchi", "DRZ": "Bauchi", "AKK": "Bauchi", "KAT": "Bauchi",
    "YEN": "Bayelsa", "KMR": "Bayelsa", "KMK": "Bayelsa", "NEM": "Bayelsa", "GBB": "Bayelsa", "SAG": "Bayelsa", "SPR": "Bayelsa",
    "BEN": "Benue", "PKG": "Benue", "GBK": "Benue", "MKD": "Benue", "OTU": "Benue",
    "BAM": "Borno", "BBU": "Borno", "DAM": "Borno", "DKW": "Borno", "HWL": "Borno", "MAI": "Borno", "MUG": "Borno",
    "DUK": "Cross River", "CAL": "Cross River", "IKM": "Cross River", "OBU": "Cross River", "UGE": "Cross River",
    "ABH": "Delta", "AGB": "Delta", "BMA": "Delta", "BUR": "Delta", "DET": "Delta", "DNB": "Delta", "DSZ": "Delta", "ASB": "Delta", "WAR": "Delta", "UGH": "Delta", "SLG": "Delta",
    "HKW": "Ebonyi", "AFK": "Ebonyi", "EZA": "Ebonyi", "OHZ": "Ebonyi",
    "ABD": "Edo", "AFZ": "Edo", "AGD": "Edo", "AUB": "Edo", "IGU": "Edo", "UBJ": "Edo", "UCH": "Edo", "OKP": "Edo",
    "ADK": "Ekiti", "EFY": "Ekiti", "EAA": "Ekiti", "GED": "Ekiti", "IER": "Ekiti", "KRE": "Ekiti", "MUE": "Ekiti", "TUN": "Ekiti", "YEK": "Ekiti",
    "AGN": "Enugu", "AGW": "Enugu", "BBG": "Enugu", "ENU": "Enugu", "AWD": "Enugu", "UDI": "Enugu", "NSK": "Enugu",
    "ABC": "Abuja", "ABJ": "Abuja", "BWR": "Abuja", "GWA": "Abuja", "KUJ": "Abuja", "KWL": "Abuja", "RBC": "Abuja", "RSH": "Abuja", "YAB": "Abuja",
    "GME": "Gombe", "BKK": "Gombe", "KMG": "Gombe", "NFD": "Gombe", "DBS": "Gombe",
    "WER": "Imo", "ORL": "Imo", "OKI": "Imo", "MGB": "Imo", "KGE": "Imo", "NKR": "Imo", "TTK": "Imo", "UMD": "Imo",
    "BBR": "Jigawa", "BMW": "Jigawa", "DTU": "Jigawa", "HJA": "Jigawa", "KZR": "Jigawa", "GML": "Jigawa", "RNG": "Jigawa",
    "KAD": "Kaduna", "DKA": "Kaduna", "MKA": "Kaduna", "ZAR": "Kaduna", "TRN": "Kaduna", "BNG": "Kaduna", "KAF": "Kaduna", "KCH": "Kaduna", "MGN": "Kaduna", "SAB": "Kaduna", "ZKW": "Kaduna",
    "KAN": "Kano", "KMC": "Kano", "BKN": "Kano", "DBT": "Kano", "ABS": "Kano", "AJG": "Kano", "BBJ": "Kano", "BCH": "Kano", "DAL": "Kano", "DGW": "Kano", "DKD": "Kano", "DTA": "Kano", "DTF": "Kano", "WUD": "Kano",
    "BAT": "Katsina", "BKR": "Katsina", "BDU": "Katsina", "BKY": "Katsina", "DRA": "Katsina", "DSM": "Katsina", "DNJ": "Katsina", "KTN": "Katsina", "FNT": "Katsina",
    "BES": "Kebbi", "BGD": "Kebbi", "DKG": "Kebbi", "BRK": "Kebbi", "ARG": "Kebbi", "YUR": "Kebbi", "JEG": "Kebbi",
    "BAS": "Kogi", "DAH": "Kogi", "DKN": "Kogi", "LKJ": "Kogi", "KBA": "Kogi", "ANC": "Kogi", "OKN": "Kogi", "AJK": "Kogi",
    "AFN": "Kwara", "ILR": "Kwara", "MUN": "Kwara", "OFF": "Kwara", "KEY": "Kwara", "LFM": "Kwara",
    "AAA": "Lagos", "AKD": "Lagos", "AGL": "Lagos", "APP": "Lagos", "BDG": "Lagos", "EKY": "Lagos", "EPE": "Lagos", "FKJ": "Lagos", "FST": "Lagos", "GGE": "Lagos", "JJJ": "Lagos", "KJA": "Lagos", "KRD": "Lagos", "KSF": "Lagos", "KTU": "Lagos", "LND": "Lagos", "LSD": "Lagos", "LSR": "Lagos", "MUS": "Lagos", "SMK": "Lagos",
    "LFA": "Nasarawa", "KFF": "Nasarawa", "AKW": "Nasarawa", "WAM": "Nasarawa", "KEG": "Nasarawa",
    "AGA": "Niger", "AGR": "Niger", "BDA": "Niger", "PAK": "Niger", "MNA": "Niger", "SUL": "Niger", "KNT": "Niger", "LAP": "Niger", "NAG": "Niger",
    "AAB": "Ogun", "ABG": "Ogun", "DED": "Ogun", "DGB": "Ogun", "AKM": "Ogun", "SGM": "Ogun", "JBD": "Ogun", "TTN": "Ogun", "WDE": "Ogun", "TRE": "Ogun", "SMG": "Ogun",
    "DEK": "Ondo", "AKR": "Ondo", "OND": "Ondo", "OWO": "Ondo", "KAA": "Ondo", "REE": "Ondo", "FFN": "Ondo", "SUA": "Ondo",
    "AAW": "Osun", "BDS": "Osun", "DTN": "Osun", "PMD": "Osun", "OSG": "Osun", "LES": "Osun", "EDE": "Osun", "GBN": "Osun", "FEE": "Osun", "SGB": "Osun",
    "AGG": "Oyo", "AJW": "Oyo", "BDJ": "Oyo", "DDA": "Oyo", "IBA": "Oyo", "IBZ": "Oyo", "NRK": "Oyo", "YEM": "Oyo", "MAP": "Oyo", "LUY": "Oyo", "AYE": "Oyo", "GNN": "Oyo",
    "BLD": "Plateau", "DMA": "Plateau", "DNG": "Plateau", "PBB": "Plateau", "PKN": "Plateau", "PTT": "Plateau", "JOS": "Plateau", "BUK": "Plateau", "QAN": "Plateau", "LAN": "Plateau",
    "ABM": "Rivers", "ABU": "Rivers", "AFM": "Rivers", "AHD": "Rivers", "DBU": "Rivers", "PHC": "Rivers", "AHO": "Rivers", "BGM": "Rivers", "BNY": "Rivers", "DEG": "Rivers", "ELE": "Rivers", "KNM": "Rivers", "OBK": "Rivers", "RUM": "Rivers", "NCH": "Rivers", "GOK": "Rivers", "BRR": "Rivers",
    "BDN": "Sokoto", "BUG": "Sokoto", "DGS": "Sokoto", "SOK": "Sokoto", "GWD": "Sokoto", "TBD": "Sokoto", "SRZ": "Sokoto", "KWE": "Sokoto",
    "BAL": "Taraba", "BBB": "Taraba", "DGA": "Taraba", "JAL": "Taraba", "MUT": "Taraba", "GKA": "Taraba", "WUK": "Taraba", "ZNG": "Taraba",
    "DPH": "Yobe", "DTR": "Yobe", "PKM": "Yobe", "BUN": "Yobe", "GUA": "Yobe", "NGR": "Yobe", "FKA": "Yobe", "MCK": "Yobe",
    "GUS": "Zamfara", "KNR": "Zamfara", "MRD": "Zamfara", "ANR": "Zamfara", "TSF": "Zamfara", "ZRM": "Zamfara"
}

# --- 2. EXCEL SETUP ---
print("Setting up Batch Excel Log File...")
if not os.path.exists(LOG_FILE):
    wb = Workbook()
    ws = wb.active
    ws.append(["Timestamp", "Image_Name", "Plate_Number", "State_of_Origin", "Country", "Confidence"])
    wb.save(LOG_FILE)

try:
    wb = load_workbook(LOG_FILE)
    ws = wb.active
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    ws.row_dimensions[1].height = 22
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for col in ['A', 'B', 'C', 'D', 'E', 'F']:
        ws.column_dimensions[col].width = 22
    wb.save(LOG_FILE)
except PermissionError:
    print(f"[ERROR] Please close {LOG_FILE} before running the script!")
    exit()

# --- 3. CORE LOGIC ---
def identify_origin_from_text(ocr_text):
    text = ocr_text.upper().replace(" ", "").replace("-", "")
    for keyword, state in NIGERIA_STATES.items():
        if keyword in text: return state
    matches = difflib.get_close_matches(text, list(NIGERIA_STATES.keys()), n=1, cutoff=0.8)
    if matches: return NIGERIA_STATES[matches[0]]
    return "Unknown"

def clean_and_format_plate(raw_text):
    clean = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    if len(clean) == 8:
        chars = list(clean)
        def fix_num(c): return {'O': '0', 'I': '1', 'S': '5', 'B': '8', 'Z': '2', 'A': '4', 'G': '6'}.get(c, c)
        def fix_let(c): return {'0': 'O', '1': 'I', '5': 'S', '8': 'B', '4': 'A', '6': 'G'}.get(c, c)
        chars[0], chars[1], chars[2] = fix_let(chars[0]), fix_let(chars[1]), fix_let(chars[2])
        chars[3], chars[4], chars[5] = fix_num(chars[3]), fix_num(chars[4]), fix_num(chars[5])
        chars[6], chars[7] = fix_let(chars[6]), fix_let(chars[7])
        return f"{''.join(chars[:3])}-{''.join(chars[3:6])}-{''.join(chars[6:])}"
    if len(clean) >= 5 and any(c.isdigit() for c in clean): return clean
    return None

# --- 4. EXECUTION ---
print("Initializing Models... Please wait.")
model = YOLO("best.pt").to(DEVICE)
reader = easyocr.Reader(['en'], gpu=False)

files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
print(f"Found {len(files)} images. Processing Batch...")

for filename in files:
    img_path = os.path.join(INPUT_FOLDER, filename)
    img = cv2.imread(img_path)
    if img is None: continue

    print(f" -> Processing: {filename}...")
    results = model(img, conf=0.15, verbose=False, device=DEVICE)

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            pad = 15
            y1_p, y2_p = max(0, y1 - pad), min(img.shape[0], y2 + pad)
            x1_p, x2_p = max(0, x1 - pad), min(img.shape[1], x2 + pad)
            crop = img[y1_p:y2_p, x1_p:x2_p]

            if crop.size > 0:
                crop_res = cv2.resize(crop, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
                gray = cv2.cvtColor(crop_res, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                contrast = clahe.apply(gray)

                # ZONED OCR
                h, w = contrast.shape
                state_zone_img = contrast[0:int(h * 0.35), 0:w]
                state_ocr_results = reader.readtext(state_zone_img)
                full_ocr_results = reader.readtext(contrast)
                
                detected_state = "Unknown"
                best_plate = None
                best_prob = 0
                
                # TIER 1
                for (_, text, prob) in state_ocr_results:
                    state_check = identify_origin_from_text(text)
                    if state_check != "Unknown": 
                        detected_state = state_check
                        break
                        
                for (_, text, prob) in full_ocr_results:
                    formatted_num = clean_and_format_plate(text)
                    if formatted_num and prob > best_prob:
                        best_plate = formatted_num
                        best_prob = prob
                
                # TIER 2: Fallback to LGA Prefix Map
                if detected_state == "Unknown" and best_plate:
                    prefix = best_plate[:3]
                    if prefix in LGA_MAP: detected_state = LGA_MAP[prefix]
                
                if best_plate:
                    # Save Evidence
                    safe_name = re.sub(r'[^A-Z0-9]', '', best_plate)
                    evidence_path = os.path.join(evidence_folder, f"EVIDENCE_{safe_name}_{filename}")
                    cv2.imwrite(evidence_path, crop)

                    # Log Data
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        wb = load_workbook(LOG_FILE)
                        ws = wb.active
                        ws.append([current_time, filename, best_plate, detected_state, "Nigeria", round(best_prob, 2)])
                        
                        last_row = ws.max_row
                        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                        for col_idx in range(1, 7): ws.cell(row=last_row, column=col_idx).fill = green_fill
                            
                        wb.save(LOG_FILE)
                    except PermissionError: pass

print(f"\nDONE! Logs saved to '{LOG_FILE}'. Evidence saved.")