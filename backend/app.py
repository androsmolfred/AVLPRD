from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
import cv2
import easyocr
from ultralytics import YOLO
from datetime import datetime
import re
import difflib
from openpyxl import load_workbook, Workbook
from openpyxl.styles import PatternFill

# Add the parent directory to the Python path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

# Enable CORS for /api/* routes with explicit configuration for preflight (OPTIONS) support
# This configuration allows cross-origin requests from any origin
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Allow all origins
        "methods": ["GET", "POST", "OPTIONS"],  # Explicitly allow OPTIONS for preflight
        "allow_headers": ["Content-Type"],  # Allow Content-Type header
        "expose_headers": ["Content-Type"],  # Expose Content-Type in response
        "supports_credentials": False
    }
})

# --- CONFIGURATION ---
DEVICE = 'cpu'
LOG_FILE = "batch_log.xlsx"
OUTPUT_FOLDER = "test_results"
EVIDENCE_FOLDER = os.path.join(OUTPUT_FOLDER, "evidence_plates")

# Nigeria states and LGA mapping (from batch_test.py)
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

LGA_MAP = {
    "ABA": "Abia", "BND": "Abia", "ACH": "Abia", "HAF": "Abia", "UMA": "Abia", "KPU": "Abia",
    "DSA": "Adamawa", "FUR": "Adamawa", "GAN": "Adamawa", "GRE": "Adamawa", "GMB": "Adamawa", "GUY": "Adamawa", "HNG": "Adamawa", "JMT": "Adamawa", "MUB": "Adamawa", "NUM": "Adamawa", "YLA": "Adamawa",
    "ABK": "Akwa Ibom", "KRT": "Akwa Ibom", "KET": "Akwa Ibom", "KST": "Akwa Ibom", "AFH": "Akwa Ibom", "AEE": "Akwa Ibom", "ETN": "Akwa Ibom", "UYO": "Akwa Ibom",
    "AGU": "Anambra", "ABN": "Anambra", "ACA": "Anambra", "AJL": "Anambra", "HAL": "Anambra", "HTE": "Anambra", "AWK": "Anambra", "NNE": "Anambra", "ONN": "Anambra",
    "BAU": "Bauchi", "BLR": "Bauchi", "BTA": "Bauchi", "DAS": "Bauchi", "DKU": "Bauchi", "DRZ": "Bauchi", "AKK": "Bauchi", "KAT": "Bauchi",
    "YEN": "Bayelsa", "KMR": "Bayelsa", "KMK": "Bayelsa", "NEM": "Bayelsa", "GBB": "Bayelsa", "SAG": "Bayelsa", "SPR": "Bayelsa",
    "BEN": "Benue", "PKG": "Benue", "GBK": "Benue", "MKD": "Benue", "OTU": "Benue",
    "BAM": "Borno", "BBU": "Borno", "BTA": "Borno", "DAM": "Borno", "DKW": "Borno", "HWL": "Borno", "MAI": "Borno", "MUG": "Borno",
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

# Initialize models
try:
    model = YOLO("best.pt").to(DEVICE)
    reader = easyocr.Reader(['en'], gpu=False)
except Exception as e:
    print(f"Warning: Could not load models: {e}")
    model = None
    reader = None

def setup_excel():
    """Setup Excel log file"""
    if not os.path.exists(LOG_FILE):
        wb = Workbook()
        ws = wb.active
        ws.append(["Timestamp", "Image_Name", "Plate_Number", "State_of_Origin", "Country", "Confidence"])
        wb.save(LOG_FILE)

def identify_origin_from_text(ocr_text):
    """Identify state from OCR text"""
    text = ocr_text.upper().replace(" ", "").replace("-", "")
    for keyword, state in NIGERIA_STATES.items():
        if keyword in text: return state
    matches = difflib.get_close_matches(text, list(NIGERIA_STATES.keys()), n=1, cutoff=0.8)
    if matches: return NIGERIA_STATES[matches[0]]
    return "Unknown"

def clean_and_format_plate(raw_text):
    """Clean and format license plate text"""
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

def process_image_file(file_path, filename):
    """Process a single image file for license plate recognition"""
    if not model or not reader:
        return {'error': 'Models not loaded'}
    
    img = cv2.imread(file_path)
    if img is None:
        return {'error': 'Could not read image file'}
    
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
                
                # TIER 1: State detection
                for (_, text, prob) in state_ocr_results:
                    state_check = identify_origin_from_text(text)
                    if state_check != "Unknown": 
                        detected_state = state_check
                        break
                        
                # TIER 2: Plate number detection
                for (_, text, prob) in full_ocr_results:
                    formatted_num = clean_and_format_plate(text)
                    if formatted_num and prob > best_prob:
                        best_plate = formatted_num
                        best_prob = prob
                
                # TIER 3: Fallback to LGA Prefix Map
                if detected_state == "Unknown" and best_plate:
                    prefix = best_plate[:3]
                    if prefix in LGA_MAP: detected_state = LGA_MAP[prefix]
                
                if best_plate:
                    # Save Evidence
                    safe_name = re.sub(r'[^A-Z0-9]', '', best_plate)
                    evidence_path = os.path.join(EVIDENCE_FOLDER, f"EVIDENCE_{safe_name}_{filename}")
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
                    except PermissionError:
                        pass

                    return {
                        'filename': filename,
                        'status': 'processed',
                        'plate_number': best_plate,
                        'state_of_origin': detected_state,
                        'confidence': round(best_prob * 100, 2),
                        'message': 'License plate detected successfully'
                    }
    
    return {
        'filename': filename,
        'status': 'no_plate_found',
        'message': 'No license plate detected in image'
    }

def process_video_file(file_path, filename):
    """Process video file for license plate recognition"""
    if not model or not reader:
        return {'error': 'Models not loaded'}
    
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        return {'error': 'Could not open video file'}
    
    results = []
    frame_count = 0
    processed_frames = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Process every 10th frame to avoid overwhelming the system
    frame_skip = 10
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # Skip frames to reduce processing load
        if frame_count % frame_skip != 0:
            continue
            
        processed_frames += 1
        
        # Process frame similar to image processing
        results_frame = process_frame(frame, f"{filename}_frame_{frame_count}")
        
        if results_frame.get('status') == 'processed':
            results.append(results_frame)
            
        # Limit processing to first 100 frames for performance
        if processed_frames >= 100:
            break
    
    cap.release()
    
    return {
        'filename': filename,
        'status': 'processed',
        'total_frames': frame_count,
        'processed_frames': processed_frames,
        'plates_found': len(results),
        'results': results,
        'message': f'Processed {processed_frames} frames, found {len(results)} license plates'
    }

def process_frame(frame, frame_name):
    """Process a single video frame for license plate recognition"""
    if not model or not reader:
        return {'error': 'Models not loaded'}
    
    results = model(frame, conf=0.15, verbose=False, device=DEVICE)
    
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            pad = 15
            y1_p, y2_p = max(0, y1 - pad), min(frame.shape[0], y2 + pad)
            x1_p, x2_p = max(0, x1 - pad), min(frame.shape[1], x2 + pad)
            crop = frame[y1_p:y2_p, x1_p:x2_p]

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
                
                # TIER 1: State detection
                for (_, text, prob) in state_ocr_results:
                    state_check = identify_origin_from_text(text)
                    if state_check != "Unknown": 
                        detected_state = state_check
                        break
                        
                # TIER 2: Plate number detection
                for (_, text, prob) in full_ocr_results:
                    formatted_num = clean_and_format_plate(text)
                    if formatted_num and prob > best_prob:
                        best_plate = formatted_num
                        best_prob = prob
                
                # TIER 3: Fallback to LGA Prefix Map
                if detected_state == "Unknown" and best_plate:
                    prefix = best_plate[:3]
                    if prefix in LGA_MAP: detected_state = LGA_MAP[prefix]
                
                if best_plate:
                    # Save Evidence
                    safe_name = re.sub(r'[^A-Z0-9]', '', best_plate)
                    evidence_path = os.path.join(EVIDENCE_FOLDER, f"EVIDENCE_{safe_name}_{frame_name}.jpg")
                    cv2.imwrite(evidence_path, crop)

                    # Log Data
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        wb = load_workbook(LOG_FILE)
                        ws = wb.active
                        ws.append([current_time, frame_name, best_plate, detected_state, "Nigeria", round(best_prob, 2)])
                        
                        last_row = ws.max_row
                        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                        for col_idx in range(1, 7): ws.cell(row=last_row, column=col_idx).fill = green_fill
                            
                        wb.save(LOG_FILE)
                    except PermissionError:
                        pass

                    return {
                        'filename': frame_name,
                        'status': 'processed',
                        'plate_number': best_plate,
                        'state_of_origin': detected_state,
                        'confidence': round(best_prob * 100, 2),
                        'message': 'License plate detected successfully'
                    }
    
    return {
        'filename': frame_name,
        'status': 'no_plate_found',
        'message': 'No license plate detected in frame'
    }

@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to the AVLPRD Backend API',
        'endpoints': {
            '/api/test': 'Test endpoint',
            '/api/process-image': 'Process uploaded image for license plate recognition',
            '/api/process-video': 'Process uploaded video for license plate recognition',
            '/api/dashboard': 'Get dashboard statistics'
        }
    })

@app.route('/api/test')
def test():
    return jsonify({
        'status': 'success',
        'message': 'Backend is working correctly',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/process-image', methods=['POST'])
def process_image():
    """
    Process uploaded image(s) for license plate recognition.
    Accepts multiple files via the 'images' key in FormData.
    Returns a JSON array with results for each processed image.
    """
    try:
        # Get all uploaded files using 'images' key (matches frontend)
        files = request.files.getlist('images')
        
        # Return 400 if no files were uploaded
        if not files or len(files) == 0:
            return jsonify({'error': 'No files uploaded', 'results': []}), 400
        
        # Filter out empty filenames
        valid_files = [f for f in files if f.filename and f.filename.strip() != '']
        
        if len(valid_files) == 0:
            return jsonify({'error': 'No valid files selected', 'results': []}), 400
        
        # Allowed image extensions
        allowed_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        
        # Validate all files before processing
        for file in valid_files:
            if not file.filename.lower().endswith(allowed_extensions):
                return jsonify({
                    'error': f'Invalid file type for {file.filename}. Please upload image files only',
                    'results': []
                }), 400
        
        # Setup upload directory
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        # List to store temporary file paths for cleanup
        temp_files = []
        results = []
        
        try:
            # Process each uploaded image file
            for file in valid_files:
                # Create unique filename to avoid conflicts
                import uuid
                unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
                file_path = os.path.join(upload_dir, unique_filename)
                temp_files.append(file_path)
                
                # Save file temporarily
                file.save(file_path)
                
                # Process the image and collect result
                result = process_image_file(file_path, file.filename)
                results.append(result)
            
            # Return all results as a JSON array
            return jsonify({
                'status': 'success',
                'total_files': len(valid_files),
                'processed_count': sum(1 for r in results if r.get('status') == 'processed'),
                'not_found_count': sum(1 for r in results if r.get('status') == 'no_plate_found'),
                'results': results
            }), 200
            
        finally:
            # Clean up ALL temporary files after processing (even if errors occur)
            for file_path in temp_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as cleanup_error:
                    print(f"Warning: Could not delete temp file {file_path}: {cleanup_error}")
    
    except Exception as e:
        # Return 500 for any unexpected server errors
        return jsonify({
            'error': f'Server error processing images: {str(e)}',
            'results': []
        }), 500

@app.route('/api/process-video', methods=['POST'])
def process_video():
    """Process uploaded video for license plate recognition"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            return jsonify({'error': 'Invalid file type. Please upload a video file'}), 400
        
        # Save uploaded file temporarily
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        file.save(file_path)
        
        # Process video frames
        results = process_video_file(file_path, file.filename)
        
        # Clean up temporary file
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard')
def dashboard():
    """Get dashboard statistics"""
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({
                "total": 0,
                "states": {},
                "avg_confidence": 0,
                "recent": []
            })
        
        import pandas as pd
        df = pd.read_excel(LOG_FILE)

        total = len(df)
        states = df['State_of_Origin'].value_counts().to_dict()
        avg_conf = round(df['Confidence'].astype(float).mean(), 2) if total > 0 else 0

        recent = df.tail(10).to_dict(orient="records")

        return jsonify({
            "total": total,
            "states": states,
            "avg_confidence": avg_conf,
            "recent": recent
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export-analytics')
def export_analytics():
    """Export all analytics data"""
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({'error': 'No data available to export'}), 404
        
        import pandas as pd
        df = pd.read_excel(LOG_FILE)
        
        # Convert to list of dictionaries
        records = df.to_dict(orient='records')
        
        # Get summary statistics
        total = len(df)
        states = df['State_of_Origin'].value_counts().to_dict()
        avg_conf = round(df['Confidence'].astype(float).mean(), 2) if total > 0 else 0
        
        return jsonify({
            'status': 'success',
            'data': records,
            'summary': {
                'total_detections': total,
                'states_covered': len(states),
                'average_confidence': avg_conf,
                'state_distribution': states
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== LIVE MONITORING ENDPOINT ====================
# This endpoint provides real-time detection data for the live monitoring feature
# It polls the latest detections and returns them in a format the frontend can display

live_detection_buffer = []  # In-memory buffer for recent live detections
MAX_BUFFER_SIZE = 50  # Keep last 50 detections

@app.route('/api/live-data')
def live_data():
    """
    Returns live detection data for real-time monitoring.
    This endpoint is polled by the frontend at regular intervals.
    
    Returns:
        - total: Total number of detections ever recorded
        - recent: Array of recent detections (from Excel log)
        - live_detections: Array of newly added detections (in-memory buffer)
        - timestamp: Server timestamp for sync
    """
    try:
        # Initialize response data
        response_data = {
            'status': 'success',
            'total': 0,
            'recent': [],
            'live_detections': live_detection_buffer.copy(),  # Return copy of buffer
            'timestamp': datetime.now().isoformat(),
            'message': 'Live data endpoint working'
        }
        
        # Read data from Excel log if it exists
        if os.path.exists(LOG_FILE):
            try:
                import pandas as pd
                df = pd.read_excel(LOG_FILE)
                response_data['total'] = len(df)
                # Return last 20 detections as "recent"
                response_data['recent'] = df.tail(20).to_dict(orient='records')
            except Exception as excel_error:
                print(f"Error reading Excel file: {excel_error}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in live_data endpoint: {e}")  # Log server-side error
        return jsonify({
            'status': 'error',
            'error': str(e),
            'total': 0,
            'recent': [],
            'live_detections': [],
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/live-data/add', methods=['POST'])
def add_live_detection():
    """
    Add a detection to the live monitoring buffer.
    Called internally when a plate is detected during live processing.
    
    Expects JSON body with: plate_number, state_of_origin, confidence, filename
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Create detection record
        detection = {
            'plate_number': data.get('plate_number', 'UNKNOWN'),
            'state_of_origin': data.get('state_of_origin', 'Unknown'),
            'confidence': data.get('confidence', 0),
            'filename': data.get('filename', 'live'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to buffer (at the beginning for most recent first)
        live_detection_buffer.insert(0, detection)
        
        # Trim buffer to max size
        while len(live_detection_buffer) > MAX_BUFFER_SIZE:
            live_detection_buffer.pop()
        
        return jsonify({
            'status': 'success',
            'detection': detection,
            'buffer_size': len(live_detection_buffer)
        })
        
    except Exception as e:
        print(f"Error adding live detection: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connection-test')
def connection_test():
    """
    Simple endpoint to test frontend-backend connectivity.
    Returns basic info about the server state.
    """
    return jsonify({
        'status': 'success',
        'message': 'Backend connection successful',
        'server_time': datetime.now().isoformat(),
        'models_loaded': model is not None and reader is not None,
        'endpoints': {
            'test': '/api/test',
            'dashboard': '/api/dashboard',
            'process_image': '/api/process-image',
            'process_video': '/api/process-video',
            'live_data': '/api/live-data',
            'export_analytics': '/api/export-analytics',
            'connection_test': '/api/connection-test'
        }
    })

if __name__ == '__main__':
    # Setup directories and Excel file
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    os.makedirs(EVIDENCE_FOLDER, exist_ok=True)
    setup_excel()
    
    print("Starting AVLPRD Backend Server...")
    print("Models loaded successfully" if model and reader else "Warning: Models not loaded")
    print("Server running at http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
