# import cv2
# import easyocr
# import pandas as pd
# from ultralytics import YOLO
# from datetime import datetime
# import os
# import re
# import difflib
# from openpyxl.styles import PatternFill, Font, Alignment

# # --- CONFIGURATION ---
# INPUT_FOLDER = "test_images"       
# OUTPUT_FOLDER = "test_results"     
# CONF_THRESHOLD = 0.20              

# os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# # --- 1. KNOWLEDGE BASE ---
# LGA_MAP = {
#     "KRD": "Lagos", "APP": "Lagos", "LND": "Lagos", "MUS": "Lagos",
#     "EKY": "Lagos", "FKJ": "Lagos", "GGE": "Lagos", "LSR": "Lagos",
#     "KTU": "Lagos", "RSH": "Abuja (FCT)", "ABC": "Abuja (FCT)",
#     "KUJ": "Abuja (FCT)", "BWR": "Abuja (FCT)", "MKA": "Kaduna",
#     "DKA": "Kaduna", "KAN": "Kano", "PHC": "Rivers"
# }

# NIGERIA_STATES = {
#     "ABJ": "Abuja (FCT)", "ABUJA": "Abuja (FCT)", "FCT": "Abuja (FCT)",
#     "BEN": "Benue", "BENUE": "Benue", "KOG": "Kogi", "KOGI": "Kogi",
#     "KWA": "Kwara", "KWARA": "Kwara", "NAS": "Nasarawa", "NASARAWA": "Nasarawa",
#     "NIG": "Niger", "NIGER": "Niger", "PLA": "Plateau", "PLATEAU": "Plateau", "JOS": "Plateau",
#     "ADA": "Adamawa", "ADAMAWA": "Adamawa", "BAU": "Bauchi", "BAUCHI": "Bauchi",
#     "BOR": "Borno", "BORNO": "Borno", "GOM": "Gombe", "GOMBE": "Gombe",
#     "TAR": "Taraba", "TARABA": "Taraba", "YOB": "Yobe", "YOBE": "Yobe",
#     "JIG": "Jigawa", "JIGAWA": "Jigawa", "KAD": "Kaduna", "KADUNA": "Kaduna",
#     "KAN": "Kano", "KANO": "Kano", "KAT": "Katsina", "KATSINA": "Katsina",
#     "KEB": "Kebbi", "KEBBI": "Kebbi", "SOK": "Sokoto", "SOKOTO": "Sokoto",
#     "ZAM": "Zamfara", "ZAMFARA": "Zamfara", "ABI": "Abia", "ABIA": "Abia",
#     "ANA": "Anambra", "ANAMBRA": "Anambra", "EBO": "Ebonyi", "EBONYI": "Ebonyi",
#     "ENU": "Enugu", "ENUGU": "Enugu", "IMO": "Imo", "AKW": "Akwa Ibom", "AKWA": "Akwa Ibom",
#     "IBOM": "Akwa Ibom", "BAY": "Bayelsa", "BAYELSA": "Bayelsa", "CRO": "Cross River",
#     "CROSS": "Cross River", "DEL": "Delta", "DELTA": "Delta", "EDO": "Edo",
#     "RIV": "Rivers", "RIVERS": "Rivers", "PHC": "Rivers", "PH": "Rivers",
#     "EKI": "Ekiti", "EKITI": "Ekiti", "LAG": "Lagos", "LAGOS": "Lagos",
#     "CENTRE": "Lagos", "LND": "Lagos", "OGU": "Ogun", "OGUN": "Ogun",
#     "OND": "Ondo", "ONDO": "Ondo", "SUN": "Ondo", "OSU": "Osun", "OSUN": "Osun", "OYO": "Oyo"
# }

# def identify_state(text, plate_number=""):
#     clean_text = text.upper().replace(" ", "").replace("-", "")
#     for keyword, full_name in NIGERIA_STATES.items():
#         if keyword in clean_text: return full_name
#     if len(plate_number) > 3:
#         prefix = plate_number[:3].upper()
#         if prefix in LGA_MAP: return LGA_MAP[prefix]
#     matches = difflib.get_close_matches(clean_text, list(NIGERIA_STATES.keys()), n=1, cutoff=0.8)
#     if matches: return NIGERIA_STATES[matches[0]]
#     return "Unknown"

# # --- 2. CLEANERS ---
# def clean_plate_text(raw_text):
#     clean = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
#     if len(clean) > 10: return "Unreadable (Noise)"
#     if len(clean) < 6: return clean 
#     chars = list(clean)
#     def fix_num(c): return {'O': '0', 'I': '1', 'S': '5', 'B': '8', 'Z': '2', 'A': '4', 'G': '6'}.get(c, c)
#     def fix_let(c): return {'0': 'O', '1': 'I', '5': 'S', '8': 'B', '4': 'A', '6': 'G'}.get(c, c)
#     if len(chars) == 8:
#         chars[0], chars[1], chars[2] = fix_let(chars[0]), fix_let(chars[1]), fix_let(chars[2])
#         chars[3], chars[4], chars[5] = fix_num(chars[3]), fix_num(chars[4]), fix_num(chars[5])
#         chars[6], chars[7] = fix_let(chars[6]), fix_let(chars[7])
#         return f"{''.join(chars[:3])}-{''.join(chars[3:6])}-{''.join(chars[6:])}"
#     return "".join(chars)

# def clean_general_plate(raw_text):
#     text = raw_text.upper()
#     SLOGANS = ["FEDERAL REPUBLIC OF NIGERIA", "FEDERAL", "REPUBLIC", "NIGERIA", "CENTRE OF EXCELLENCE", "CENTER OF EXCELLENCE", "HEARTBEAT OF THE NATION", "THE STATE OF HARMONY", "COAL CITY STATE", "SALT OF THE NATION", "LAGOS", "ABUJA", "FCT", "PEACE AND TOURISM"]
#     for slogan in SLOGANS: text = text.replace(slogan, "")
#     return re.sub(r'[^A-Z0-9-]', '', text)

# # --- 3. LOAD MODELS ---
# print("1. Loading Models...")
# model_ng = YOLO("best.pt")
# reader = easyocr.Reader(['en'], gpu=False)

# log_file = "batch_results_log.xlsx"
# df_log = pd.DataFrame(columns=["Time_Stamp", "Image_Name", "Model", "Origin_Capital", "Plate_Number", "Confidence"])

# # --- 4. PROCESS FUNCTION ---
# def process_batch():
#     global df_log
    
#     # Create evidence folder
#     evidence_folder = os.path.join(OUTPUT_FOLDER, "evidence_plates")
#     os.makedirs(evidence_folder, exist_ok=True)

#     files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
#     print(f"2. Found {len(files)} images. Processing...")

#     for filename in files:
#         img_path = os.path.join(INPUT_FOLDER, filename)
#         img = cv2.imread(img_path)
#         if img is None: continue

#         print(f"   -> Processing: {filename}...")
#         current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
#         # TEST 1: NIGERIA
#         results_ng = model_ng(img, verbose=False)
#         for result in results_ng:
#             for box in result.boxes:
#                 score = float(box.conf[0])
#                 if score > CONF_THRESHOLD:
#                     x1, y1, x2, y2 = map(int, box.xyxy[0])
#                     plate_crop = img[y1:y2, x1:x2]
                    
#                     # SAVE EVIDENCE
#                     gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
#                     contrast = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
#                     ocr_res = reader.readtext(contrast)
#                     detected_state = "Unknown"
#                     potential_numbers = []
#                     for (_, text, prob) in ocr_res:
#                         if prob > 0.1 and len(text) > 2:
#                             found_state = identify_state(text)
#                             if found_state != "Unknown": detected_state = found_state 
#                             else: potential_numbers.append(clean_plate_text(text))
#                     detected_number = max(potential_numbers, key=len) if potential_numbers else "Unreadable"
#                     if detected_state == "Unknown": detected_state = identify_state("", detected_number)
                    
#                     safe_name = re.sub(r'[^A-Z0-9]', '', detected_number)
#                     evidence_path = os.path.join(evidence_folder, f"EVIDENCE_{safe_name}_{filename}")
#                     cv2.imwrite(evidence_path, plate_crop)

#                     cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                     cv2.putText(img, f"{detected_number}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
#                     new_entry = {"Time_Stamp": current_time, "Image_Name": filename, "Model": "Nigeria", "Origin_Capital": detected_state, "Plate_Number": detected_number, "Confidence": round(score, 2)}
#                     df_log = pd.concat([df_log, pd.DataFrame([new_entry])], ignore_index=True)

       
#     # --- 5. COLORFUL EXCEL SAVING (WITH HEIGHT & ALIGNMENT) ---
#     with pd.ExcelWriter(log_file, engine='openpyxl') as writer:
#         df_log.to_excel(writer, index=False, sheet_name='Sheet1')
#         ws = writer.sheets['Sheet1']
        
#         # Styles
#         header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid") # Dark Blue
#         header_font = Font(color="FFFFFF", bold=True)
#         green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
#         red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        
#         # --- NEW: Set Header Height to 22 ---
#         ws.row_dimensions[1].height = 22

#         # Apply to Header
#         for cell in ws[1]:
#             cell.fill = header_fill
#             cell.font = header_font
#             # --- NEW: Middle and Center Align ---
#             cell.alignment = Alignment(horizontal="center", vertical="center")

#         # Apply to Data Rows
#         for row in range(2, ws.max_row + 1):
#             model_cell = ws[f'C{row}']
#             if model_cell.value == "Nigeria":
#                 for col in range(1, 7): ws.cell(row=row, column=col).fill = green_fill
#             elif model_cell.value == "International":
#                 for col in range(1, 7): ws.cell(row=row, column=col).fill = red_fill

#         # Set Column Widths to 25
#         for col in ['A', 'B', 'C', 'D', 'E', 'F']:
#             ws.column_dimensions[col].width = 25
            
#     print(f"\n3. DONE! Colorful formatted log saved to '{log_file}'. Evidence saved.")

# process_batch()


import cv2
import easyocr
import pandas as pd
import numpy as np
from ultralytics import YOLO
from datetime import datetime
import os
import re
import difflib
from openpyxl.styles import PatternFill, Font, Alignment

# --- CONFIGURATION ---
INPUT_FOLDER = "test_images"       
OUTPUT_FOLDER = "test_results"     
CONF_THRESHOLD = 0.20              

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- 1. KNOWLEDGE BASE ---
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

NIGERIA_STATES = {
    "ABJ": "Abuja (FCT)", "ABUJA": "Abuja (FCT)", "FCT": "Abuja (FCT)",
    "BEN": "Benue", "BENUE": "Benue", "KOG": "Kogi", "KOGI": "Kogi",
    "KWA": "Kwara", "KWARA": "Kwara", "NAS": "Nasarawa", "NASARAWA": "Nasarawa",
    "NIG": "Niger", "NIGER": "Niger", "PLA": "Plateau", "PLATEAU": "Plateau", "JOS": "Plateau",
    "ADA": "Adamawa", "ADAMAWA": "Adamawa", "BAU": "Bauchi", "BAUCHI": "Bauchi",
    "BOR": "Borno", "BORNO": "Borno", "GOM": "Gombe", "GOMBE": "Gombe",
    "TAR": "Taraba", "TARABA": "Taraba", "YOB": "Yobe", "YOBE": "Yobe",
    "JIG": "Jigawa", "JIGAWA": "Jigawa", "KAD": "Kaduna", "KADUNA": "Kaduna",
    "KAN": "Kano", "KANO": "Kano", "KAT": "Katsina", "KATSINA": "Katsina",
    "KEB": "Kebbi", "KEBBI": "Kebbi", "SOK": "Sokoto", "SOKOTO": "Sokoto",
    "ZAM": "Zamfara", "ZAMFARA": "Zamfara", "ABI": "Abia", "ABIA": "Abia",
    "ANA": "Anambra", "ANAMBRA": "Anambra", "EBO": "Ebonyi", "EBONYI": "Ebonyi",
    "ENU": "Enugu", "ENUGU": "Enugu", "IMO": "Imo", "AKW": "Akwa Ibom", "AKWA": "Akwa Ibom",
    "IBOM": "Akwa Ibom", "BAY": "Bayelsa", "BAYELSA": "Bayelsa", "CRO": "Cross River",
    "CROSS": "Cross River", "DEL": "Delta", "DELTA": "Delta", "EDO": "Edo",
    "RIV": "Rivers", "RIVERS": "Rivers", "PHC": "Rivers", "PH": "Rivers",
    "EKI": "Ekiti", "EKITI": "Ekiti", "LAG": "Lagos", "LAGOS": "Lagos",
    "CENTRE": "Lagos", "LND": "Lagos", "OGU": "Ogun", "OGUN": "Ogun",
    "OND": "Ondo", "ONDO": "Ondo", "SUN": "Ondo", "OSU": "Osun", "OSUN": "Osun", "OYO": "Oyo"
}

def identify_state(text, plate_number=""):
    clean_text = text.upper().replace(" ", "").replace("-", "")
    for keyword, full_name in NIGERIA_STATES.items():
        if keyword in clean_text: return full_name
    if len(plate_number) > 3:
        prefix = plate_number[:3].upper()
        if prefix in LGA_MAP: return LGA_MAP[prefix]
    matches = difflib.get_close_matches(clean_text, list(NIGERIA_STATES.keys()), n=1, cutoff=0.8)
    if matches: return NIGERIA_STATES[matches[0]]
    return "Unknown"

# --- 2. ADVANCED CLEANING & PRE-PROCESSING ---
def clean_and_format_plate(raw_text):
    """Enforces Nigerian format and auto-corrects common OCR mistakes."""
    clean = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    
    # If it matches the exact 8-character Nigerian length, apply smart fixes
    if len(clean) == 8:
        chars = list(clean)
        def fix_num(c): return {'O': '0', 'I': '1', 'S': '5', 'B': '8', 'Z': '2', 'A': '4', 'G': '6'}.get(c, c)
        def fix_let(c): return {'0': 'O', '1': 'I', '5': 'S', '8': 'B', '4': 'A', '6': 'G'}.get(c, c)
        
        # Format: 3 Letters - 3 Numbers - 2 Letters
        chars[0], chars[1], chars[2] = fix_let(chars[0]), fix_let(chars[1]), fix_let(chars[2])
        chars[3], chars[4], chars[5] = fix_num(chars[3]), fix_num(chars[4]), fix_num(chars[5])
        chars[6], chars[7] = fix_let(chars[6]), fix_let(chars[7])
        
        formatted = f"{''.join(chars[:3])}-{''.join(chars[3:6])}-{''.join(chars[6:])}"
        return formatted, True
    
    # Fallback for partial reads
    if len(clean) >= 5:
        return clean, False
    return "Unreadable", False

def get_best_ocr(plate_crop, ocr_reader):
    """Applies CLAHE contrast and sharpening before reading text."""
    if plate_crop.size == 0: return []
    
    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
    
    # Adaptive Contrast (CLAHE) - Great for high sunlight/shadows
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast = clahe.apply(gray)
    
    # Sharpening kernel
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(contrast, -1, kernel)
    
    return ocr_reader.readtext(sharpened)

# --- 3. LOAD MODELS ---
print("1. Loading Models...")
model_ng = YOLO("best.pt")
reader = easyocr.Reader(['en'], gpu=False)

log_file = "batch_results_log.xlsx"
df_log = pd.DataFrame(columns=["Time_Stamp", "Image_Name", "Model", "Origin_Capital", "Plate_Number", "Confidence"])

# --- 4. PROCESS FUNCTION ---
def process_batch():
    global df_log
    
    # Create evidence folder
    evidence_folder = os.path.join(OUTPUT_FOLDER, "evidence_plates")
    os.makedirs(evidence_folder, exist_ok=True)

    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"2. Found {len(files)} images. Processing...")

    for filename in files:
        img_path = os.path.join(INPUT_FOLDER, filename)
        img = cv2.imread(img_path)
        if img is None: continue

        print(f"   -> Processing: {filename}...")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # TEST 1: NIGERIA
        results_ng = model_ng(img, verbose=False)
        for result in results_ng:
            for box in result.boxes:
                score = float(box.conf[0])
                if score > CONF_THRESHOLD:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # Add padding to avoid clipping the edges
                    pad = 15
                    y1_pad, y2_pad = max(0, y1-pad), min(img.shape[0], y2+pad)
                    x1_pad, x2_pad = max(0, x1-pad), min(img.shape[1], x2+pad)
                    plate_crop = img[y1_pad:y2_pad, x1_pad:x2_pad]
                    
                    ocr_res = get_best_ocr(plate_crop, reader)
                    
                    detected_state = "Unknown"
                    potential_numbers = []
                    best_number = "Unreadable"
                    
                    for (_, text, prob) in ocr_res:
                        if prob > 0.15 and len(text) > 2:
                            # 1. Check if the text is a state/slogan
                            found_state = identify_state(text)
                            if found_state != "Unknown": 
                                detected_state = found_state 
                            
                            # 2. Check if the text is the main plate number
                            clean_text, is_perfect_match = clean_and_format_plate(text)
                            if is_perfect_match:
                                best_number = clean_text
                                break # Stop searching, we found a perfect formatted plate
                            elif clean_text != "Unreadable":
                                potential_numbers.append(clean_text)
                    
                    # Fallback if no perfect 8-character match was found
                    if best_number == "Unreadable" and potential_numbers:
                        best_number = max(potential_numbers, key=len)
                    
                    # Fallback state detection based on plate prefix
                    if detected_state == "Unknown" and best_number != "Unreadable": 
                        detected_state = identify_state("", best_number)
                    
                    # SAVE EVIDENCE
                    safe_name = re.sub(r'[^A-Z0-9]', '', best_number)
                    evidence_path = os.path.join(evidence_folder, f"EVIDENCE_{safe_name}_{filename}")
                    cv2.imwrite(evidence_path, plate_crop)

                    # DRAW VISUALS
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(img, f"{best_number}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # LOG
                    new_entry = {"Time_Stamp": current_time, "Image_Name": filename, "Model": "Nigeria", "Origin_Capital": detected_state, "Plate_Number": best_number, "Confidence": round(score, 2)}
                    df_log = pd.concat([df_log, pd.DataFrame([new_entry])], ignore_index=True)

       
    # --- 5. COLORFUL EXCEL SAVING ---
    with pd.ExcelWriter(log_file, engine='openpyxl') as writer:
        df_log.to_excel(writer, index=False, sheet_name='Sheet1')
        ws = writer.sheets['Sheet1']
        
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        
        ws.row_dimensions[1].height = 22

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row in range(2, ws.max_row + 1):
            plate_cell = ws[f'E{row}'] # Column E is Plate_Number
            if plate_cell.value and plate_cell.value != "Unreadable":
                for col in range(1, 7): ws.cell(row=row, column=col).fill = green_fill

        for col in ['A', 'B', 'C', 'D', 'E', 'F']:
            ws.column_dimensions[col].width = 25
            
    print(f"\n3. DONE! Colorful formatted log saved to '{log_file}'. Evidence saved.")

process_batch()