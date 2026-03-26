# AVLPRD - Automatic Vehicle License Plate Recognition Dashboard

A full-stack web application for automatic vehicle license plate recognition using React.js frontend and Flask backend.

## Project Structure

```
AVLPRD/
├── frontend/           # React.js frontend application
├── backend/            # Flask backend API
│   ├── app.py         # Main Flask application
│   ├── run.py         # Application runner
│   └── requirements.txt # Backend dependencies
├── uploads/           # Directory for uploaded files
└── README.md         # This file
```

---

## Backend Setup and Running

### Prerequisites

- Python 3.10+
- pip
- At least 4GB RAM (for YOLO model loading)

### Installation

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. (Optional) Create a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   **Note**: The requirements include:
   - `flask==2.3.3` - Web framework
   - `flask-cors==4.0.0` - CORS support (handles cross-origin requests)
   - `opencv-python==4.8.0.76` - Image processing
   - `torch==2.0.1` - PyTorch for YOLO model
   - `ultralytics` - YOLO model handling
   - `easyocr` - Text recognition

### Running the Backend

1. Ensure you're in the backend directory:
   ```bash
   cd backend
   ```

2. Start the Flask development server:
   ```bash
   python run.py
   # OR directly:
   python app.py
   ```

3. You should see output similar to:
   ```
   Starting AVLPRD Backend Server...
   Models loaded successfully
   Server running at http://localhost:5000
   ```

4. The API will be available at `http://localhost:5000`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Welcome page with API documentation |
| `/api/test` | GET | Test endpoint to verify backend is working |
| `/api/process-image` | POST | Process uploaded image for license plate recognition |
| `/api/process-video` | POST | Process uploaded video for license plate recognition |
| `/api/dashboard` | GET | Get dashboard statistics |

### Testing the Backend

**Using curl:**
```bash
# Test endpoint
curl http://localhost:5000/api/test

# Expected response:
# {"message": "Backend is working correctly", "status": "success", "timestamp": "..."}
```

**Using browser:**
Open `http://localhost:5000/` in your browser to see the API documentation.

---

## CORS (Cross-Origin Resource Sharing)

### What is CORS?

CORS is a security feature in browsers that restricts web pages from making requests to a different domain than the one that served the web page. Since your frontend runs on `http://localhost:3000` and backend on `http://localhost:5000`, they are considered different origins.

### How CORS is Handled in This Project

Your backend has CORS enabled in `backend/app.py`:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

This configuration:
- Allows all origins to access all API endpoints
- Supports all HTTP methods (GET, POST, etc.)
- Allows common headers

### Checking for CORS Errors

#### 1. Browser Console Check (Most Common)

1. Open your browser's Developer Tools (F12 or right-click → Inspect)
2. Go to the **Console** tab
3. Look for error messages like:
   - `Access to fetch at 'http://localhost:5000/api/test' from origin 'http://localhost:3000' has been blocked by CORS policy`
   - `No 'Access-Control-Allow-Origin' header is present on the requested resource`

#### 2. Network Tab Check

1. In Developer Tools, go to the **Network** tab
2. Make a request to the backend
3. Check the response headers for:
   - `Access-Control-Allow-Origin: *`

#### 3. Test CORS with curl

```bash
# Test with CORS headers check
curl -I http://localhost:5000/api/test

# Look for these headers in the response:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Methods: GET, POST, OPTIONS
# Access-Control-Allow-Headers: Content-Type
```

### Common CORS Errors and Solutions

#### Error 1: "No Access-Control-Allow-Origin header"

**Cause**: CORS not properly configured on backend.

**Solution**: 
- Ensure `flask-cors` is installed: `pip install flask-cors`
- Verify `CORS(app)` is in your `app.py`

#### Error 2: "Method not allowed"

**Cause**: Browser sends OPTIONS request before the actual request (preflight).

**Solution**: Flask-CORS should handle this automatically. If not, add:

```python
@app.route('/api/process-image', methods=['OPTIONS'])
def handle_options():
    return '', 200
```

#### Error 3: "Credentials not supported"

**Cause**: Trying to send cookies/auth with CORS.

**Solution**: If using credentials, update CORS configuration:

```python
from flask_cors import CORS

CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000", "supports_credentials": True}})
```

#### Error 4: Backend not running

**Cause**: Backend server is down.

**Solution**:
1. Check if backend is running: `curl http://localhost:5000/api/test`
2. If not, start it: `python backend/run.py`

### Frontend-Backend Connection Checklist

If you're experiencing issues, verify these items:

- [ ] Backend server is running on port 5000
- [ ] No firewall blocking port 5000
- [ ] `flask-cors` is installed in the backend
- [ ] Browser console shows no CORS errors
- [ ] Frontend API calls use correct URL (`http://localhost:5000`)

---

## Frontend Setup

### Prerequisites

- Node.js 16+
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

### Running the Frontend

1. Start the development server:
   ```bash
   npm start
   ```

2. The React application will be available at `http://localhost:3000`

### Important: Start Backend First

Before running the frontend, ensure the backend is running:

1. Terminal 1 - Start Backend:
   ```bash
   cd backend
   python run.py
   ```

2. Terminal 2 - Start Frontend:
   ```bash
   cd frontend
   npm start
   ```

---

## Features

- **Image Processing**: Upload and process images for license plate recognition
- **Video Processing**: Upload and process videos for license plate recognition
- **Nigeria Plate Recognition**: Specialized recognition for Nigerian license plates with state identification
- **Dashboard**: Web-based dashboard for monitoring and managing recognition tasks
- **Evidence Storage**: Automatically saves detected plates as evidence images

---

## Development

### Backend Development

- Flask with CORS enabled for cross-origin requests
- YOLO model for object detection (license plates)
- EasyOCR for text recognition
- File uploads handled with temporary storage in `uploads/` directory

### Frontend Development

- React.js with modern JavaScript
- Component-based architecture
- RESTful API integration with the Flask backend

---

## Production Deployment

### Backend

1. Set `debug=False` in `run.py` for production
2. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 app:app
   ```

### Frontend

1. Build the production version:
   ```bash
   npm run build
   ```

2. Serve the built files with a web server (nginx, Apache, etc.)

---

## Troubleshooting

### Backend Issues

| Issue | Solution |
|-------|----------|
| "Module not found" | Run `pip install -r requirements.txt` |
| "Port 5000 in use" | Kill existing process or change port in `run.py` |
| "Model not loaded" | Ensure `best.pt` exists in project root |
| "Permission error" | Check file permissions for logs |

### Frontend Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" | Ensure backend is running |
| "CORS error" | Check browser console, see CORS section above |
| "Build fails" | Delete `node_modules` and run `npm install` again |

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request