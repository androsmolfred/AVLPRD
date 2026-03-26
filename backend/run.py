#!/usr/bin/env python3
"""
Flask application runner for the AVLPRD backend.
This script starts the Flask development server.
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Ensure uploads directory exists
    os.makedirs('uploads', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)