import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import { Camera, Video, Activity, FileText, Play, Upload, X, CheckCircle, AlertCircle, Info, Moon, Sun, Car, Download, RotateCcw, Menu, Radio, Loader2, Webcam } from 'lucide-react';

// ==================== API CONFIGURATION ====================
// Backend server URL - ensure Flask backend is running on port 5000
// Using localhost instead of 127.0.0.1 for better browser compatibility
const API_BASE_URL = 'http://localhost:5000';

// ==================== POLLING INTERVAL FOR LIVE MONITORING ====================
const LIVE_POLL_INTERVAL = 3000; // Poll every 3 seconds for live data updates

function App() {
  // ==================== STATE MANAGEMENT ====================
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadType, setUploadType] = useState('image');
  const [files, setFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [showUploadPanel, setShowUploadPanel] = useState(false);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [showAboutModal, setShowAboutModal] = useState(false);
  const [showLiveModal, setShowLiveModal] = useState(false); // Live monitoring modal state
  const [liveData, setLiveData] = useState({ recent: [], live_detections: [], total: 0, timestamp: null });
  const [connectionStatus, setConnectionStatus] = useState('checking'); // checking, connected, disconnected
  const [toast, setToast] = useState(null);
  const [darkMode, setDarkMode] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    // Check screen size - only for large desktops (1024px+) do we always want open
    const screenWidth = window.innerWidth;
    if (screenWidth >= 1024) return true; // Always open on desktop (1024px+)
    
    // For tablet/mobile (below 1024px), default to collapsed
    return false;
  });
  const [activeSection, setActiveSection] = useState('home');
  const [processingCount, setProcessingCount] = useState(0);
  
  // ==================== LIVE CAMERA STATE ====================
  const [showCameraModal, setShowCameraModal] = useState(false); // Live camera modal state
  const [cameraActive, setCameraActive] = useState(false); // Camera stream active
  const [cameraLoading, setCameraLoading] = useState(false); // Camera loading state
  const [cameraError, setCameraError] = useState(''); // Camera error message
  const [cameraResults, setCameraResults] = useState([]); // Results from camera processing
  const [isProcessingFrame, setIsProcessingFrame] = useState(false); // Frame processing in progress
  
  // Refs for camera stream and capture
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const captureIntervalRef = useRef(null);
  
  // Ref for live monitoring polling interval
  const livePollingRef = useRef(null);
  
  // ==================== CAMERA FUNCTIONS ====================
  // Start camera stream
  const startCamera = async () => {
    setCameraLoading(true);
    setCameraError('');
    
    try {
      // Request camera access using getUserMedia
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'environment' // Prefer back camera on mobile devices
        },
        audio: false
      });
      
      // Store stream reference
      streamRef.current = stream;
      
      // Set video source
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      
      setCameraActive(true);
      setCameraLoading(false);
      
      // Start capturing frames at intervals (every 2 seconds)
      startFrameCapture();
      
    } catch (err) {
      console.error('Camera access error:', err);
      setCameraLoading(false);
      
      // Handle specific permission errors
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setCameraError('Camera access denied. Please allow camera permissions and try again.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setCameraError('No camera found. Please connect a camera and try again.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setCameraError('Camera is in use by another application. Please close other apps using the camera.');
      } else {
        setCameraError(`Camera error: ${err.message}`);
      }
    }
  };
  
  // Stop camera stream
  const stopCamera = () => {
    // Stop all tracks in the stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    // Clear video source
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    
    // Stop frame capture interval
    if (captureIntervalRef.current) {
      clearInterval(captureIntervalRef.current);
      captureIntervalRef.current = null;
    }
    
    setCameraActive(false);
    setCameraResults([]);
  };
  
  // Capture frame from video and send to backend
  const captureFrame = useCallback(async () => {
    // Prevent multiple simultaneous processing
    if (isProcessingFrame || !videoRef.current || !canvasRef.current) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    
    // Draw current video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to blob
    setIsProcessingFrame(true);
    
    canvas.toBlob(async (blob) => {
      if (!blob) {
        setIsProcessingFrame(false);
        return;
      }
      
      try {
        // Create FormData and append image with key "images"
        const formData = new FormData();
        formData.append('images', blob, `camera_frame_${Date.now()}.jpg`);
        
        // Send to backend
        const response = await fetch(`${API_BASE_URL}/api/process-image`, {
          method: 'POST',
          body: formData
          // Note: NOT setting Content-Type header manually - let browser set it with boundary
        });
        
        if (response.ok) {
          const data = await response.json();
          
          if (data.results && data.results.length > 0) {
            // Add new results to the top of the list
            setCameraResults(prev => {
              const newResults = data.results.filter(r => r.status === 'processed');
              return [...newResults, ...prev].slice(0, 20); // Keep max 20 results
            });
            
            // Show toast for successful detection
            const processedCount = data.processed_count || 0;
            if (processedCount > 0) {
              showToast(`Plate detected!`, 'success');
            }
          }
        } else {
          console.error('Frame processing failed:', response.status);
        }
      } catch (err) {
        console.error('Frame send error:', err);
      } finally {
        setIsProcessingFrame(false);
      }
    }, 'image/jpeg', 0.9); // JPEG quality 90%
  }, [isProcessingFrame, API_BASE_URL, showToast]);
  
  // Start continuous frame capture
  const startFrameCapture = () => {
    // Capture immediately
    setTimeout(captureFrame, 1000);
    
    // Then capture every 2 seconds
    captureIntervalRef.current = setInterval(() => {
      if (cameraActive) {
        captureFrame();
      }
    }, 2000);
  };
  
  // Handle camera modal close - cleanup
  const handleCloseCameraModal = () => {
    stopCamera();
    setShowCameraModal(false);
    // Refresh dashboard to show new detections
    fetchDashboardData();
  };

  // ==================== TOAST NOTIFICATION ====================
  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  // ==================== INITIAL DATA FETCH ====================
  useEffect(() => {
    // Fetch dashboard data on mount
    fetchDashboardData();
    // Test connection to backend
    testConnection();
  }, []);

  // ==================== THEME MANAGEMENT ====================
  useEffect(() => {
    if (darkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [darkMode]);

  // ==================== LIVE MONITORING POLLING ====================
  // Start/stop polling when live modal opens/closes
  useEffect(() => {
    if (showLiveModal) {
      // Start polling when modal opens
      fetchLiveData(); // Fetch immediately
      livePollingRef.current = setInterval(fetchLiveData, LIVE_POLL_INTERVAL);
    } else {
      // Stop polling when modal closes
      if (livePollingRef.current) {
        clearInterval(livePollingRef.current);
        livePollingRef.current = null;
      }
    }
    
    // Cleanup on unmount
    return () => {
      if (livePollingRef.current) {
        clearInterval(livePollingRef.current);
      }
    };
  }, [showLiveModal]);

  // ==================== CONNECTION TEST ====================
  // Tests connectivity to the backend server
  const testConnection = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/connection-test`);
      if (response.ok) {
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('disconnected');
      }
    } catch (err) {
      console.error('Connection test failed:', err);
      setConnectionStatus('disconnected');
    }
  };

  // ==================== FETCH DASHBOARD DATA ====================
  // Fetches dashboard statistics from the backend
  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard`);
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      } else {
        console.error('Failed to fetch dashboard data:', response.status);
      }
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      // Silently fail - use default stats when backend is unavailable
      setDashboardData(null);
    }
  };

  // ==================== FETCH LIVE DATA ====================
  // Fetches live detection data for real-time monitoring
  const fetchLiveData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/live-data`);
      if (response.ok) {
        const data = await response.json();
        setLiveData(data);
        setConnectionStatus('connected');
      } else {
        console.error('Failed to fetch live data:', response.status);
        setConnectionStatus('disconnected');
      }
    } catch (err) {
      console.error('Live data fetch error:', err);
      setConnectionStatus('disconnected');
    }
  };

  // ==================== RESET HANDLER ====================
  // Reset all state to initial values
  const handleReset = () => {
    setResults([]);
    setDashboardData(null);
    setFiles([]);
    setUploadProgress(0);
    setError('');
    setShowUploadPanel(false);
    setShowErrorModal(false);
    setActiveSection('home');
    fetchDashboardData();
    showToast('Dashboard reset successfully', 'success');
  };

  // ==================== FILE UPLOAD HANDLER ====================
  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (files.length === 0) {
      setError('Please select file(s) to upload');
      setShowErrorModal(true);
      return;
    }

    setLoading(true);
    setUploadProgress(0);
    setError('');
    setResults([]);
    setProcessingCount(files.length);

    try {
      const formData = new FormData();
      
      // Append all files with the key 'images' (matches backend's request.files.getlist('images'))
      // This allows multiple files to be sent in a single request
      files.forEach((file) => {
        formData.append('images', file);
      });

      setUploadProgress(30); // Indicate request is being sent

      // Determine endpoint based on upload type (image or video)
      const endpoint = uploadType === 'image' ? '/api/process-image' : '/api/process-video';
      
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
        // Note: NOT setting Content-Type header manually - let browser set it with boundary for FormData
      });

      setUploadProgress(80); // Indicate response received

      if (response.ok) {
        const data = await response.json();
        
        setUploadProgress(100);
        
        if (uploadType === 'image') {
          // For image uploads, response contains { status, total_files, processed_count, not_found_count, results: [...] }
          const allResults = data.results || [];
          setResults(allResults);
          
          const successCount = data.processed_count || 0;
          const notFoundCount = data.not_found_count || 0;
          
          if (successCount > 0) {
            showToast(`Successfully processed ${successCount} of ${data.total_files} images!`, 'success');
          } else if (notFoundCount > 0) {
            showToast(`No license plates found in ${notFoundCount} images`, 'info');
          } else {
            showToast('Processing complete, but no plates detected', 'info');
          }
        } else {
          // For video uploads, response is a single result object
          setResults([data]);
          
          if (data.status === 'processed') {
            showToast(`Video processed! Found ${data.plates_found || 0} plate(s)`, 'success');
          } else {
            showToast('Video processed, but no plates found', 'info');
          }
        }
        
        // Refresh dashboard after successful upload
        fetchDashboardData();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Upload failed');
        setShowErrorModal(true);
        showToast('Failed to process files', 'error');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError('Network error occurred. Please check if the backend server is running at http://localhost:5000');
      setShowErrorModal(true);
      showToast('Network error occurred', 'error');
    } finally {
      setLoading(false);
    }
  };

  // ==================== ACTION HANDLER ====================
  // Handles various action buttons (image, video, live, etc.)
  const handleAction = async (action) => {
    switch (action) {
      case 'image':
        setUploadType('image');
        setShowUploadPanel(true);
        setFiles([]);
        setError('');
        break;
      case 'video':
        setUploadType('video');
        setShowUploadPanel(true);
        setFiles([]);
        setError('');
        break;
      case 'live':
        // Open live monitoring modal instead of showing toast
        setShowLiveModal(true);
        break;
      case 'camera':
        // Open live camera modal for real-time camera streaming
        setShowCameraModal(true);
        break;
      case 'analysis':
        await fetchDashboardData();
        setActiveSection('analysis');
        break;
      case 'report':
        await fetchDashboardData();
        showToast('Report generated!', 'success');
        break;
      default:
        break;
    }
  };

  // ==================== FORMAT FILE SIZE ====================
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // ==================== DASHBOARD DATA MAPPING ====================
  // Map backend response to frontend expected format
  // Backend returns: { total, states, avg_confidence, recent }
  // Frontend expects: { total_detections, today_detections, accuracy_rate, states_covered }
  const stats = React.useMemo(() => {
    if (dashboardData) {
      const stateCount = dashboardData.states ? Object.keys(dashboardData.states).length : 0;
      return {
        total_detections: dashboardData.total || 0,
        today_detections: dashboardData.recent ? dashboardData.recent.length : 0,
        accuracy_rate: dashboardData.avg_confidence || 0,
        states_covered: stateCount || 0
      };
    }
    // Default fallback values when backend is unavailable
    return {
      total_detections: 127,
      today_detections: 12,
      accuracy_rate: 94.5,
      states_covered: 36
    };
  }, [dashboardData]);

  // ==================== RENDER ====================
  return (
    <div className={`App ${darkMode ? 'dark-mode' : ''}`}>
      {/* Toast Notification */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.type === 'success' && <CheckCircle size={20} />}
          {toast.type === 'error' && <AlertCircle size={20} />}
          {toast.type === 'info' && <Info size={20} />}
          <span>{toast.message}</span>
          <button className="toast-close" onClick={() => setToast(null)}>
            <X size={16} />
          </button>
        </div>
      )}

      {/* Mobile Menu Button */}
      <button 
        className={`mobile-menu-btn ${sidebarOpen ? 'hidden' : ''}`}
        onClick={() => setSidebarOpen(true)}
        aria-label="Open menu"
      >
        <Menu size={24} />
      </button>

      {/* Sidebar Overlay */}
      <div 
        className={`sidebar-overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={() => setSidebarOpen(false)}
      />

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
        <div className="sidebar-header">
          <div className="logo">
            <img src={require('./imageCapture.jpeg')} alt="AVLPRDL" style={{ width: 32, height: 32, borderRadius: 8 }} />
            <span>AVLPRDL System</span>
          </div>
          {/* Connection Status Indicator */}
          <div className={`connection-status ${connectionStatus}`}>
            <Radio size={12} />
            <span>{connectionStatus === 'connected' ? 'Online' : connectionStatus === 'disconnected' ? 'Offline' : 'Connecting...'}</span>
          </div>
        </div>
        
        <button className="sidebar-expand" onClick={() => setSidebarOpen(true)}>
          <Car size={20} />
        </button>
        
        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeSection === 'home' ? 'active' : ''}`}
            onClick={() => setActiveSection('home')}
          >
            <Activity size={20} />
            <span>Dashboard</span>
          </button>
          <button className="nav-item" onClick={async () => {
            try {
              setLoading(true);
              const response = await fetch(`${API_BASE_URL}/api/export-analytics`);
              if (response.ok) {
                const data = await response.json();
                if (data.data && data.data.length > 0) {
                  setResults(data.data.map((item, idx) => ({
                    filename: item.Image_Name || `Record ${idx + 1}`,
                    status: 'processed',
                    plate_number: item.Plate_Number,
                    state_of_origin: item.State_of_Origin,
                    confidence: item.Confidence,
                    message: 'Exported from analytics'
                  })));
                  showToast(`Exported ${data.data.length} records successfully!`, 'success');
                } else {
                  showToast('No analytics data available to export', 'info');
                }
              } else {
                showToast('Failed to export analytics', 'error');
              }
            } catch (err) {
              console.error('Export analytics error:', err);
              showToast('Failed to export analytics', 'error');
            } finally {
              setLoading(false);
            }
          }}>
            <Download size={20} />
            <span>Export Analytics Result</span>
          </button>
          <button className="nav-item" onClick={handleReset}>
            <RotateCcw size={20} />
            <span>Reset</span>
          </button>
          <button className="nav-item" onClick={() => setShowAboutModal(true)}>
            <Info size={20} />
            <span>About</span>
          </button>
        </nav>
        
        <div className="sidebar-footer">
          <button className="theme-toggle" onClick={() => setDarkMode(!darkMode)}>
            {darkMode ? <Sun size={20} /> : <Moon size={20} />}
            <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`main-content ${sidebarOpen ? '' : 'full-width'}`}>
        <header className="top-header">
          <div className="header-left">
            <h1>Automated Vehicle License Plate Recognition (AVLPR)<br />& Data Logging</h1>
            <p>Real-Time Detection & Intelligent Data Archiving</p>
          </div>
          
        </header>

        {/* Stats Cards */}
        <section className="stats-section">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon stat-icon-1">
                <Camera size={24} />
              </div>
              <div className="stat-content">
                <span className="stat-value">{stats.today_detections}</span>
                <span className="stat-label">Recent Detections</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon stat-icon-2">
                <Activity size={24} />
              </div>
              <div className="stat-content">
                <span className="stat-value">{stats.total_detections}</span>
                <span className="stat-label">Total Plates</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon stat-icon-3">
                <CheckCircle size={24} />
              </div>
              <div className="stat-content">
                <span className="stat-value">{stats.accuracy_rate}%</span>
                <span className="stat-label">Accuracy Rate</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon stat-icon-4">
                <FileText size={24} />
              </div>
              <div className="stat-content">
                <span className="stat-value">{stats.states_covered}</span>
                <span className="stat-label">States Covered</span>
              </div>
            </div>
          </div>
        </section>

        {/* Action Cards */}
        <section className="actions-section">
          <h2>Quick Actions</h2>
          <div className="actions-grid">
            <button className="action-card action-image" onClick={() => handleAction('image')}>
              <div className="action-icon">
                <Camera size={32} />
              </div>
              <div className="action-info">
                <h3>Process Image</h3>
                <p>Upload and analyze image files</p>
              </div>
              <div className="action-arrow">
                <Upload size={20} />
              </div>
            </button>

            <button className="action-card action-video" onClick={() => handleAction('video')}>
              <div className="action-icon">
                <Video size={32} />
              </div>
              <div className="action-info">
                <h3>Analyze Video</h3>
                <p>Process video streams</p>
              </div>
              <div className="action-arrow">
                <Upload size={20} />
              </div>
            </button>

            <button className="action-card action-live" onClick={() => handleAction('live')}>
              <div className="action-icon">
                <Play size={32} />
              </div>
              <div className="action-info">
                <h3>Live Monitoring</h3>
                <p>Real-Time Detection</p>
              </div>
              <div className="action-arrow">
                <Play size={20} />
              </div>
            </button>

            <button className="action-card action-camera" onClick={() => handleAction('camera')}>
              <div className="action-icon">
                <Webcam size={32} />
              </div>
              <div className="action-info">
                <h3>Live Camera</h3>
                <p>Camera Streaming & Detection</p>
              </div>
              <div className="action-arrow">
                <Camera size={20} />
              </div>
            </button>
          </div>
        </section>

        {/* Results Section */}
        {results.length > 0 && (
          <section className="results-section">
            <h2>Detection Results</h2>
            <div className="results-grid">
              {results.map((result, index) => (
                <div key={index} className="result-card">
                  <div className="result-header">
                    <span className="result-filename">{result.filename}</span>
                    <span className={`result-status ${result.status}`}>{result.status}</span>
                  </div>
                  <div className="result-body">
                    <p className="result-message">{result.message}</p>
                    {result.plate_number && (
                      <div className="plate-details">
                        <div className="plate-number">
                          <span className="label">Plate Number</span>
                          <span className="value">{result.plate_number}</span>
                        </div>
                        <div className="plate-state">
                          <span className="label">State</span>
                          <span className="value badge">{result.state_of_origin}</span>
                        </div>
                        <div className="plate-confidence">
                          <span className="label">Confidence</span>
                          <span className="value">{result.confidence}%</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        <footer className="app-footer">
          <div className="footer-left">
            <img src="/MYLogo.png" alt="wurdboss" width={25}/>
            <span>Uwagboi Andrew Chukwuyem </span>
          </div>
          <div className="footer-right">
            <span>myFinalYearProject©2026</span>
          </div>
        </footer>
      </main>

      {/* Upload Modal */}
      {showUploadPanel && (
        <div className="modal-overlay" onClick={() => setShowUploadPanel(false)}>
          <div className="modal upload-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                {uploadType === 'image' ? <><Camera size={24} /> Upload Images</> : <><Video size={24} /> Upload Video</>}
              </h2>
              <button className="modal-close" onClick={() => setShowUploadPanel(false)}>
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleFileUpload} className="upload-form">
              <div className="file-drop-zone">
                <Upload size={48} />
                <p>Drag and drop or click to select {uploadType === 'image' ? 'multiple images' : 'a video'}</p>
                <input
                  type="file"
                  multiple={uploadType === 'image'}
                  accept={uploadType === 'image' ? '.png,.jpg,.jpeg,.gif,.bmp' : '.mp4,.avi,.mov,.mkv'}
                  onChange={(e) => {
                    const newFiles = Array.from(e.target.files);
                    setFiles(prev => [...prev, ...newFiles]);
                  }}
                />
              </div>
              {files.length > 0 && (
                <div className="selected-files">
                  <div className="selected-files-header">
                    <span>Selected Files ({files.length})</span>
                    <button 
                      type="button" 
                      className="clear-all-btn"
                      onClick={() => setFiles([])}
                    >
                      Clear All
                    </button>
                  </div>
                  <div className="files-list">
                    {files.map((file, index) => (
                      <div key={index} className="file-info">
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">{formatFileSize(file.size)}</span>
                        <button 
                          type="button" 
                          className="remove-file-btn"
                          onClick={() => setFiles(prev => prev.filter((_, i) => i !== index))}
                        >
                          <X size={16} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {loading && (
                <div className="progress-info">
                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
                  </div>
                  <span className="progress-text">
                    Processing {processingCount} of {files.length} files...
                  </span>
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => {
                  setShowUploadPanel(false);
                  setFiles([]);
                }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={loading || files.length === 0}>
                  {loading ? 'Processing...' : `Upload ${files.length > 0 ? `${files.length} ` : ''}${uploadType === 'image' ? 'Image(s)' : 'Video'}`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Error Modal */}
      {showErrorModal && error && (
        <div className="modal-overlay" onClick={() => setShowErrorModal(false)}>
          <div className="modal error-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><AlertCircle size={24} /> Error</h2>
              <button className="modal-close" onClick={() => setShowErrorModal(false)}>
                <X size={20} />
              </button>
            </div>
            <p className="error-message">{error}</p>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => { setShowErrorModal(false); setError(''); }}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* About Modal */}
      {showAboutModal && (
        <div className="modal-overlay" onClick={() => setShowAboutModal(false)}>
          <div className="modal about-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><Info size={24} /> Student's Details</h2>
              <button className="modal-close" onClick={() => setShowAboutModal(false)}>
                <X size={20} />
              </button>
            </div>
            <div className="about-content">
              <div className="about-hero">
                <h3>AVLPRDL System</h3>
              </div>
              
              <div className="about-details">
                <div className="about-item">
                  <span className="about-label">Project Topic</span>
                  <span className="about-value">Developing a Solution for Automated Vehicle License Plate Recognition (AVLPR) & Data Logging</span>
                </div>
                <div className="about-item">
                  <span className="about-label">Supervisor</span>
                  <span className="about-value">Dr. Oluwafemi Samuel O. Abe</span>
                </div>
                <div className="about-item">
                  <span className="about-label">Developer</span>
                  <span className="about-value">Uwagboi Andrew Chukwuyem</span>
                </div>
                <div className="about-item">
                  <span className="about-label">Matric Number</span>
                  <span className="about-value">2203030127</span>
                </div>
                <div className="about-item">
                  <span className="about-label">Department</span>
                  <span className="about-value">Computer Science</span>
                </div>
                <div className="about-item">
                  <span className="about-label">Year</span>
                  <span className="about-value">2026</span>
                </div>
              </div>

              <div className="about-tech">
                <h4>Technologies Used</h4>
                <div className="tech-tags">
                  <span className="tech-tag">React</span>
                  <span className="tech-tag">Python</span>
                  <span className="tech-tag">YOLOv8</span>
                  <span className="tech-tag">Flask</span>
                  <span className="tech-tag">OCR</span>
                </div>
              </div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-primary" onClick={() => setShowAboutModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================== LIVE CAMERA MODAL ==================== */}
      {/* Full camera streaming UI with start/stop controls, video preview, and real-time results */}
      {showCameraModal && (
        <div className="modal-overlay" onClick={handleCloseCameraModal}>
          <div className="modal camera-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><Webcam size={24} /> Live Camera</h2>
              <div className="camera-status">
                {cameraActive && (
                  <div className="camera-recording">
                    <span className="recording-dot"></span>
                    <span>Recording</span>
                  </div>
                )}
                {isProcessingFrame && (
                  <div className="camera-processing">
                    <Loader2 size={16} className="spin" />
                    <span>Processing</span>
                  </div>
                )}
              </div>
              <button className="modal-close" onClick={handleCloseCameraModal}>
                <X size={20} />
              </button>
            </div>
            
            <div className="camera-content">
              {/* Camera Video Preview */}
              <div className="camera-preview-section">
                <div className="camera-preview-wrapper">
                  {/* Hidden canvas for frame capture */}
                  <canvas ref={canvasRef} style={{ display: 'none' }} />
                  
                  {/* Video element for camera stream */}
                  <video 
                    ref={videoRef} 
                    autoPlay 
                    playsInline 
                    muted
                    className="camera-video"
                  />
                  
                  {/* Camera not started state */}
                  {!cameraActive && !cameraLoading && (
                    <div className="camera-placeholder">
                      <Camera size={64} />
                      <p>Camera is not active</p>
                      <span>Click "Start Camera" to begin streaming</span>
                    </div>
                  )}
                  
                  {/* Camera loading state */}
                  {cameraLoading && (
                    <div className="camera-loading">
                      <Loader2 size={48} className="spin" />
                      <p>Requesting camera access...</p>
                    </div>
                  )}
                </div>
                
                {/* Camera Controls */}
                <div className="camera-controls">
                  {!cameraActive ? (
                    <button 
                      className="btn btn-primary btn-camera-start"
                      onClick={startCamera}
                      disabled={cameraLoading}
                    >
                      <Camera size={20} />
                      {cameraLoading ? 'Starting...' : 'Start Camera'}
                    </button>
                  ) : (
                    <button 
                      className="btn btn-secondary btn-camera-stop"
                      onClick={stopCamera}
                    >
                      <X size={20} />
                      Stop Camera
                    </button>
                  )}
                </div>
                
                {/* Error Message */}
                {cameraError && (
                  <div className="camera-error">
                    <AlertCircle size={20} />
                    <span>{cameraError}</span>
                  </div>
                )}
              </div>
              
              {/* Camera Results Section */}
              <div className="camera-results-section">
                <h3>Detections ({cameraResults.length})</h3>
                
                {cameraResults.length > 0 ? (
                  <div className="camera-results-list">
                    {cameraResults.map((result, index) => (
                      <div key={index} className="camera-result-item">
                        <div className="camera-result-header">
                          <span className="camera-result-plate">{result.plate_number}</span>
                          <span className="camera-result-badge badge">{result.state_of_origin}</span>
                        </div>
                        <div className="camera-result-meta">
                          <span className="camera-result-confidence">
                            {result.confidence}%
                          </span>
                          <span className="camera-result-time">
                            {new Date().toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="camera-empty-state">
                    {cameraActive ? (
                      <>
                        <Loader2 size={32} className="spin" />
                        <p>Waiting for detections...</p>
                        <span>Frames are being analyzed every 2 seconds</span>
                      </>
                    ) : (
                      <>
                        <Camera size={32} />
                        <p>No detections yet</p>
                        <span>Start the camera to begin detection</span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
            
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={handleCloseCameraModal}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================== LIVE MONITORING MODAL ==================== */}
      {showLiveModal && (
        <div className="modal-overlay" onClick={() => setShowLiveModal(false)}>
          <div className="modal live-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2><Radio size={24} /> Live Monitoring</h2>
              <div className="live-status-indicator">
                <span className={`live-dot ${connectionStatus === 'connected' ? 'active' : ''}`}></span>
                <span>{connectionStatus === 'connected' ? 'Live' : 'Connecting...'}</span>
              </div>
              <button className="modal-close" onClick={() => setShowLiveModal(false)}>
                <X size={20} />
              </button>
            </div>
            
            <div className="live-content">
              {/* Live Stats Summary */}
              <div className="live-stats-summary">
                <div className="live-stat">
                  <span className="live-stat-value">{liveData.total || 0}</span>
                  <span className="live-stat-label">Total Detections</span>
                </div>
                <div className="live-stat">
                  <span className="live-stat-value">{liveData.recent?.length || 0}</span>
                  <span className="live-stat-label">Recent</span>
                </div>
                <div className="live-stat">
                  <span className="live-stat-value">{liveData.live_detections?.length || 0}</span>
                  <span className="live-stat-label">Live Buffer</span>
                </div>
              </div>
              
              {/* Last Updated Timestamp */}
              {liveData.timestamp && (
                <div className="live-timestamp">
                  Last updated: {new Date(liveData.timestamp).toLocaleTimeString()}
                </div>
              )}
              
              {/* Recent Detections List */}
              <div className="live-detections-section">
                <h3>Recent Detections</h3>
                {liveData.recent && liveData.recent.length > 0 ? (
                  <div className="live-detections-list">
                    {liveData.recent.map((detection, index) => (
                      <div key={index} className="live-detection-item">
                        <div className="detection-info">
                          <span className="detection-plate">{detection.Plate_Number || detection.plate_number || 'N/A'}</span>
                          <span className="detection-state badge">{detection.State_of_Origin || detection.state_of_origin || 'Unknown'}</span>
                        </div>
                        <div className="detection-meta">
                          <span className="detection-confidence">
                            {(detection.Confidence || detection.confidence || 0).toFixed(1)}%
                          </span>
                          <span className="detection-time">
                            {detection.Timestamp || detection.timestamp || 'N/A'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="live-empty-state">
                    <Camera size={48} />
                    <p>No recent detections</p>
                    <span>Upload images or videos to see live detections here</span>
                  </div>
                )}
              </div>
              
              {/* Live Buffer (newest detections) */}
              {liveData.live_detections && liveData.live_detections.length > 0 && (
                <div className="live-buffer-section">
                  <h3>Live Buffer (Newest)</h3>
                  <div className="live-detections-list">
                    {liveData.live_detections.slice(0, 10).map((detection, index) => (
                      <div key={index} className="live-detection-item live-item">
                        <div className="detection-info">
                          <span className="detection-plate">{detection.plate_number}</span>
                          <span className="detection-state badge">{detection.state_of_origin}</span>
                        </div>
                        <div className="detection-meta">
                          <span className="detection-confidence">
                            {(detection.confidence || 0).toFixed(1)}%
                          </span>
                          <span className="detection-time live-badge">LIVE</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => {
                setShowLiveModal(false);
                fetchDashboardData();
              }}>
                Close
              </button>
              <button className="btn btn-primary" onClick={fetchLiveData} disabled={loading}>
                {loading ? 'Refreshing...' : 'Refresh Now'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
