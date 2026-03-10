import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import cv2
import easyocr
import pandas as pd
from ultralytics import YOLO
from datetime import datetime
import os
import re
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment

# --- 1. CONFIGURATION ---
LOG_FILE = "video_log.xlsx"
VIDEO_PATH = "video_feed_car_test.mp4" # Ensure this file is in your AVLPRDL folder

# --- NIGERIAN STATE MAP ---
NIGERIA_STATES = {
    "ABJ": "Abuja (FCT)", "FCT": "Abuja (FCT)", "ABIA": "Umuahia", "ADAMAWA": "Yola", 
    "AKWA IBOM": "Uyo", "ANAMBRA": "Awka", "ANA": "Awka", "BAUCHI": "Bauchi", 
    "BAYELSA": "Yenagoa", "BENUE": "Makurdi", "BEN": "Makurdi", "BORNO": "Maiduguri", 
    "CROSS RIVER": "Calabar", "DELTA": "Asaba", "DEL": "Asaba", "EBONYI": "Abakaliki", 
    "EDO": "Benin City", "EKITI": "Ado-Ekiti", "ENUGU": "Enugu", "ENU": "Enugu", 
    "GOMBE": "Gombe", "IMO": "Owerri", "JIGAWA": "Dutse", "KADUNA": "Kaduna", 
    "KAD": "Kaduna", "KANO": "Kano", "KAN": "Kano", "KATSINA": "Katsina", 
    "KEBBI": "Birnin Kebbi", "KOGI": "Lokoja", "KWARA": "Ilorin", "LAGOS": "Ikeja", 
    "LAG": "Ikeja", "NASARAWA": "Lafia", "NIGER": "Minna", "OGUN": "Abeokuta", 
    "OGU": "Abeokuta", "ONDO": "Akure", "OND": "Akure", "OSUN": "Osogbo", 
    "OYO": "Ibadan", "PLATEAU": "Jos", "RIVERS": "Port Harcourt", 
    "PHC": "Port Harcourt", "SOKOTO": "Sokoto", "TARABA": "Jalingo", 
    "YOBE": "Damaturu", "ZAMFARA": "Gusau"
}

LGA_MAP = {
    # --- LAGOS STATE ---
    "AAA": "Lagos", "AKD": "Lagos", "AGL": "Lagos", "APP": "Lagos", 
    "BDG": "Lagos", "EKY": "Lagos", "EPE": "Lagos", "FKJ": "Lagos", 
    "FST": "Lagos", "GGE": "Lagos", "JJJ": "Lagos", "KJA": "Lagos", 
    "KRD": "Lagos", "KSF": "Lagos", "KTU": "Lagos", "LND": "Lagos", 
    "LSD": "Lagos", "LSR": "Lagos", "MUS": "Lagos", "SMK": "Lagos",
    
    # --- ABUJA (FCT) ---
    "ABC": "Abuja", "ABJ": "Abuja", "BWR": "Abuja", "GWA": "Abuja", 
    "KUJ": "Abuja", "KWL": "Abuja", "RBC": "Abuja", "RSH": "Abuja", 
    "YAB": "Abuja",
    
    # --- KANO STATE ---
    "KAN": "Kano",  "KMC": "Kano",  "BCH": "Kano",  "BGW": "Kano", 
    "BKN": "Kano",  "DBT": "Kano",  "GWA": "Kano",  "BBJ": "Kano",
    "WUD": "Kano",  "TUD": "Kano",  "RNO": "Kano",  "MDB": "Kano",
    
    # --- RIVERS STATE ---
    "PHC": "Rivers", "AHO": "Rivers", "BGM": "Rivers", "BNY": "Rivers", 
    "DEG": "Rivers", "ELE": "Rivers", "KNM": "Rivers", "OBK": "Rivers",
    "RUM": "Rivers", "NCH": "Rivers",
    
    # --- KADUNA STATE ---
    "KAD": "Kaduna", "DKA": "Kaduna", "MKA": "Kaduna", "ZAR": "Kaduna", 
    "TRN": "Kaduna", "KAF": "Kaduna", "KCH": "Kaduna", "MGN": "Kaduna",
    "SAB": "Kaduna", "ZKW": "Kaduna",
    
    # --- OYO STATE ---
    "IBA": "Oyo", "IBZ": "Oyo", "NRK": "Oyo", "YEM": "Oyo", "MAP": "Oyo",
    "BDJ": "Oyo", "AGD": "Oyo", "LUY": "Oyo", "AYE": "Oyo", "GNN": "Oyo",
    
    # --- OGUN STATE ---
    "ABG": "Ogun", "AAB": "Ogun", "AKM": "Ogun", "SGM": "Ogun", "JBD": "Ogun",
    "KJA": "Ogun", "TTN": "Ogun", "WDE": "Ogun", "TRE": "Ogun", "SMG": "Ogun",

    # 1. ABIA
    "ABA": "Abia", "BND": "Abia", "ACH": "Abia", "HAF": "Abia", "UMA": "Abia", "KPU": "Abia",
    # 2. ADAMAWA
    "DSA": "Adamawa", "FUR": "Adamawa", "GAN": "Adamawa", "GRE": "Adamawa", "GMB": "Adamawa", "GUY": "Adamawa", "HNG": "Adamawa", "JMT": "Adamawa", "MUB": "Adamawa", "NUM": "Adamawa", "YLA": "Adamawa",
    # 3. AKWA IBOM
    "ABK": "Akwa Ibom", "KRT": "Akwa Ibom", "KET": "Akwa Ibom", "KST": "Akwa Ibom", "AFH": "Akwa Ibom", "AEE": "Akwa Ibom", "ETN": "Akwa Ibom", "UYO": "Akwa Ibom",
    # 4. ANAMBRA
    "AGU": "Anambra", "ABN": "Anambra", "ACA": "Anambra", "AJL": "Anambra", "HAL": "Anambra", "HTE": "Anambra", "AWK": "Anambra", "NNE": "Anambra", "ONN": "Anambra",
    # 5. BAUCHI
    "BAU": "Bauchi", "BLR": "Bauchi", "BTA": "Bauchi", "DAS": "Bauchi", "DKU": "Bauchi", "DRZ": "Bauchi", "AKK": "Bauchi", "KAT": "Bauchi",
    # 6. BAYELSA
    "YEN": "Bayelsa", "KMR": "Bayelsa", "KMK": "Bayelsa", "NEM": "Bayelsa", "GBB": "Bayelsa", "SAG": "Bayelsa", "SPR": "Bayelsa",
    # 7. BENUE
    "BEN": "Benue", "PKG": "Benue", "GBK": "Benue", "MKD": "Benue", "OTU": "Benue",
    # 8. BORNO
    "BAM": "Borno", "BBU": "Borno", "DAM": "Borno", "DKW": "Borno", "HWL": "Borno", "MAI": "Borno", "MUG": "Borno",
    # 9. CROSS RIVER
    "DUK": "Cross River", "CAL": "Cross River", "IKM": "Cross River", "OBU": "Cross River", "UGE": "Cross River",
    # 10. DELTA
    "ABH": "Delta", "AGB": "Delta", "BMA": "Delta", "BUR": "Delta", "DET": "Delta", "DNB": "Delta", "DSZ": "Delta", "ASB": "Delta", "WAR": "Delta", "UGH": "Delta", "SLG": "Delta",
    # 11. EBONYI
    "HKW": "Ebonyi", "ABK": "Ebonyi", "AFK": "Ebonyi", "EZA": "Ebonyi", "OHZ": "Ebonyi",
    # 12. EDO
    "ABD": "Edo", "AFZ": "Edo", "AGD": "Edo", "BEN": "Edo", "AUB": "Edo", "IGU": "Edo", "UBJ": "Edo", "UCH": "Edo", "OKP": "Edo",
    # 13. EKITI
    "ADK": "Ekiti", "EFY": "Ekiti", "EAA": "Ekiti", "GED": "Ekiti", "IER": "Ekiti", "KRE": "Ekiti", "MUE": "Ekiti", "TUN": "Ekiti", "YEK": "Ekiti",
    # 14. ENUGU
    "AGN": "Enugu", "AGW": "Enugu", "BBG": "Enugu", "ENU": "Enugu", "AWD": "Enugu", "UDI": "Enugu", "NSK": "Enugu",
    # 15. FCT - ABUJA
    "ABC": "Abuja", "ABJ": "Abuja", "BWR": "Abuja", "GWA": "Abuja", "KUJ": "Abuja", "KWL": "Abuja", "RBC": "Abuja", "RSH": "Abuja", "YAB": "Abuja",
    # 16. GOMBE
    "GME": "Gombe", "BKK": "Gombe", "KMG": "Gombe", "NFD": "Gombe", "DKU": "Gombe", "DBS": "Gombe",
    # 17. IMO
    "WER": "Imo", "ORL": "Imo", "OKI": "Imo", "MGB": "Imo", "KGE": "Imo", "NKR": "Imo", "TTK": "Imo", "UMD": "Imo",
    # 18. JIGAWA
    "BBR": "Jigawa", "BMW": "Jigawa", "DTU": "Jigawa", "HJA": "Jigawa", "KZR": "Jigawa", "GML": "Jigawa", "RNG": "Jigawa",
    # 19. KADUNA
    "KAD": "Kaduna", "DKA": "Kaduna", "MKA": "Kaduna", "ZAR": "Kaduna", "TRN": "Kaduna", "BNG": "Kaduna", "KAF": "Kaduna", "KCH": "Kaduna", "MGN": "Kaduna", "SAB": "Kaduna", "ZKW": "Kaduna",
    # 20. KANO
    "KAN": "Kano", "KMC": "Kano", "GWA": "Kano", "BKN": "Kano", "DBT": "Kano", "ABS": "Kano", "AJG": "Kano", "BBJ": "Kano", "BCH": "Kano", "DAL": "Kano", "DGW": "Kano", "DKD": "Kano", "DTA": "Kano", "DTF": "Kano", "WUD": "Kano",
    # 21. KATSINA
    "BAT": "Katsina", "BKR": "Katsina", "BDU": "Katsina", "BKY": "Katsina", "DRA": "Katsina", "DSM": "Katsina", "DNJ": "Katsina", "KTN": "Katsina", "FNT": "Katsina",
    # 22. KEBBI
    "BES": "Kebbi", "BGD": "Kebbi", "DKG": "Kebbi", "BRK": "Kebbi", "ARG": "Kebbi", "YUR": "Kebbi", "JEG": "Kebbi",
    # 23. KOGI
    "BAS": "Kogi", "DAH": "Kogi", "DKN": "Kogi", "LKJ": "Kogi", "KBA": "Kogi", "ANC": "Kogi", "OKN": "Kogi", "AJK": "Kogi",
    # 24. KWARA
    "AFN": "Kwara", "BDU": "Kwara", "ILR": "Kwara", "MUN": "Kwara", "OFF": "Kwara", "KEY": "Kwara", "LFM": "Kwara",
    # 25. LAGOS
    "AAA": "Lagos", "AKD": "Lagos", "AGL": "Lagos", "APP": "Lagos", "BDG": "Lagos", "EKY": "Lagos", "EPE": "Lagos", "FKJ": "Lagos", "FST": "Lagos", "GGE": "Lagos", "JJJ": "Lagos", "KJA": "Lagos", "KRD": "Lagos", "KSF": "Lagos", "KTU": "Lagos", "LND": "Lagos", "LSD": "Lagos", "LSR": "Lagos", "MUS": "Lagos", "SMK": "Lagos",
    # 26. NASARAWA
    "LFA": "Nasarawa", "KFF": "Nasarawa", "AKW": "Nasarawa", "NSK": "Nasarawa", "GWA": "Nasarawa", "WAM": "Nasarawa", "KEG": "Nasarawa",
    # 27. NIGER
    "AGA": "Niger", "AGR": "Niger", "BDA": "Niger", "BKY": "Niger", "PAK": "Niger", "MNA": "Niger", "SUL": "Niger", "KNT": "Niger", "LAP": "Niger", "NAG": "Niger",
    # 28. OGUN
    "AAB": "Ogun", "ABG": "Ogun", "DED": "Ogun", "DGB": "Ogun", "AKM": "Ogun", "SGM": "Ogun", "JBD": "Ogun", "KJA": "Ogun", "TTN": "Ogun", "WDE": "Ogun", "TRE": "Ogun", "SMG": "Ogun",
    # 29. ONDO
    "DEK": "Ondo", "AKR": "Ondo", "OND": "Ondo", "OWO": "Ondo", "KAA": "Ondo", "REE": "Ondo", "FFN": "Ondo", "SUA": "Ondo",
    # 30. OSUN
    "AAW": "Osun", "BDS": "Osun", "BKN": "Osun", "DTN": "Osun", "PMD": "Osun", "OSG": "Osun", "LES": "Osun", "EDE": "Osun", "GBN": "Osun", "FEE": "Osun", "SGB": "Osun",
    # 31. OYO
    "AGG": "Oyo", "AJW": "Oyo", "BDJ": "Oyo", "DDA": "Oyo", "IBA": "Oyo", "IBZ": "Oyo", "NRK": "Oyo", "YEM": "Oyo", "MAP": "Oyo", "AGD": "Oyo", "LUY": "Oyo", "AYE": "Oyo", "GNN": "Oyo",
    # 32. PLATEAU
    "BLD": "Plateau", "DMA": "Plateau", "DNG": "Plateau", "PBB": "Plateau", "PKN": "Plateau", "PTT": "Plateau", "JOS": "Plateau", "BUK": "Plateau", "QAN": "Plateau", "LAN": "Plateau", "BKK": "Plateau",
    # 33. RIVERS
    "ABM": "Rivers", "ABU": "Rivers", "AFM": "Rivers", "AHD": "Rivers", "DBU": "Rivers", "PHC": "Rivers", "AHO": "Rivers", "BGM": "Rivers", "BNY": "Rivers", "DEG": "Rivers", "ELE": "Rivers", "KNM": "Rivers", "OBK": "Rivers", "RUM": "Rivers", "NCH": "Rivers", "GOK": "Rivers", "BRR": "Rivers",
    # 34. SOKOTO
    "BDN": "Sokoto", "BUG": "Sokoto", "DGS": "Sokoto", "SOK": "Sokoto", "GWD": "Sokoto", "TBD": "Sokoto", "SRZ": "Sokoto", "YAB": "Sokoto", "KWE": "Sokoto",
    # 35. TARABA
    "BAL": "Taraba", "BBB": "Taraba", "DGA": "Taraba", "JAL": "Taraba", "MUT": "Taraba", "GKA": "Taraba", "WUK": "Taraba", "ZNG": "Taraba",
    # 36. YOBE
    "DPH": "Yobe", "DTR": "Yobe", "PKM": "Yobe", "BUN": "Yobe", "GUA": "Yobe", "NGR": "Yobe", "FKA": "Yobe", "MCK": "Yobe",
    # 37. ZAMFARA
    "GUS": "Zamfara", "KNR": "Zamfara", "MRD": "Zamfara", "ANR": "Zamfara", "TSF": "Zamfara", "ZRM": "Zamfara", "GWA": "Zamfara", "BKN": "Zamfara"
}


def identify_origin(ocr_text, plate_number):
    text = ocr_text.upper().replace(" ", "").replace("-", "")
    for keyword, capital in NIGERIA_STATES.items():
        if keyword in text: return f"Nigeria: {keyword.title()} ({capital})"
    
    # Stricter Nigerian pattern check (e.g. ABC123DE)
    nigeria_pattern = r'^[A-Z]{3}\d{3}[A-Z]{2}$'
    if re.match(nigeria_pattern, plate_number): return "Nigeria (General)"
    return "International"

# --- 2. EXCEL STYLING ---
def format_excel_report(file_path):
    try:
        wb = load_workbook(file_path)
        ws = wb.active
        header_fill = PatternFill(start_color="002060", end_color="002060", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")
            
        for col in ws.columns:
            max_length = 0
            column_letter = col[0].column_letter
            for cell in col:
                if cell.value and len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            ws.column_dimensions[column_letter].width = max_length + 5
        wb.save(file_path)
    except Exception as e: 
        print(f"Excel Error: {e}")

# --- 3. INITIALIZATION & SAFETY CHECKS ---
if not os.path.exists(VIDEO_PATH):
    print(f"[ERROR] Video file '{VIDEO_PATH}' not found in the current folder.")
    exit()

print("Loading models... Please wait.")
model = YOLO("best.pt") # Using your custom Nigerian model
reader = easyocr.Reader(['en'], gpu=False)

cap = cv2.VideoCapture(VIDEO_PATH)
seen_plates = set()

# Window Setup
target_w, target_h = 854, 480
WINDOW_NAME = "Nigerian ALPR Video Analysis"
cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WINDOW_NAME, target_w, target_h)

# Initialize Excel
headers = ["Time_Stamp", "Model", "Origin_Capital", "Plate_Number", "Confidence"]
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=headers).to_excel(LOG_FILE, index=False)
    format_excel_report(LOG_FILE)

print(f"Starting analysis on {VIDEO_PATH}...")

# --- 4. MAIN LOOP ---
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: 
        print("End of video stream reached.")
        break

    # Run Detection
    results = model(frame, conf=0.20, verbose=False)
    
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Pad the crop to ensure EasyOCR sees the whole plate
            pad = 15
            y1_p = max(0, y1 - pad)
            y2_p = min(frame.shape[0], y2 + pad)
            x1_p = max(0, x1 - pad)
            x2_p = min(frame.shape[1], x2 + pad)
            
            plate_crop = frame[y1_p:y2_p, x1_p:x2_p]

            if plate_crop.size > 0:
                # --- NEW: Image Upscaling & CLAHE Contrast for Video Frames ---
                # 1. Upscale the cropped plate 2.5x
                plate_res = cv2.resize(plate_crop, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
                
                # 2. Grayscale & Contrast Enhancement (CLAHE)
                gray = cv2.cvtColor(plate_res, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                contrast = clahe.apply(gray)

                # 3. Read text from the enhanced image
                ocr_res = reader.readtext(contrast)

                for (_, text, prob) in ocr_res:
                    clean_num = re.sub(r'[^A-Z0-9]', '', text.upper())
                    
                    # Logic: Must be at least 5 chars, unseen, and prob > 0.25 (to account for video blur)
                    if len(clean_num) >= 5 and clean_num not in seen_plates and prob > 0.25:
                        origin = identify_origin(text, clean_num)
                        
                        # Logging
                        new_data = pd.DataFrame([{
                            "Time_Stamp": datetime.now().strftime("%H:%M:%S"), 
                            "Model": "best.pt (Nigerian)", 
                            "Origin_Capital": origin, 
                            "Plate_Number": clean_num, 
                            "Confidence": round(prob, 2)
                        }])
                        
                        with pd.ExcelWriter(LOG_FILE, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                            new_data.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
                        
                        format_excel_report(LOG_FILE)
                        seen_plates.add(clean_num)
                        print(f"[DETECTED & LOGGED] {clean_num} - Confidence: {round(prob, 2)} - {origin}")

            # Draw visual box on the frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, "Plate Detected", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display video
    display_frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
    cv2.imshow(WINDOW_NAME, display_frame)
    
    # Press 'q' to quit early
    if cv2.waitKey(1) & 0xFF == ord('q'): 
        break

cap.release()
cv2.destroyAllWindows()
print(f"Analysis complete. Logs saved to {LOG_FILE}.")