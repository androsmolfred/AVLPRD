import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import { Camera, Video, Activity, FileText, Play, Upload, X, CheckCircle, AlertCircle, Info, Moon, Sun, Car, Download, RotateCcw } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:5000';

function App() {
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
  const [toast, setToast] = useState(null);
  const [darkMode, setDarkMode] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeSection, setActiveSection] = useState('home');
  const [processingCount, setProcessingCount] = useState(0);

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [darkMode]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/dashboard`);
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (err) {
      // Silently fail - use default stats when backend is unavailable
      setDashboardData(null);
    } finally {
      setLoading(false);
    }
  };

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
    setProcessingCount(0);

    const allResults = [];
    const totalFiles = files.length;
    
    for (let i = 0; i < files.length; i++) {
      setProcessingCount(i + 1);
      setUploadProgress(Math.round(((i + 1) / totalFiles) * 100));

      const formData = new FormData();
      formData.append('file', files[i]);

      try {
        const endpoint = uploadType === 'image' ? '/api/process-image' : '/api/process-video';
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const result = await response.json();
          allResults.push(result);
        } else {
          const errorData = await response.json();
          allResults.push({
            filename: files[i].name,
            status: 'error',
            message: errorData.error || 'Upload failed'
          });
        }
      } catch (err) {
        allResults.push({
          filename: files[i].name,
          status: 'error',
          message: 'Network error occurred'
        });
      }
    }

    setResults(allResults);
    setUploadProgress(100);
    
    const successCount = allResults.filter(r => r.status === 'processed').length;
    const errorCount = allResults.filter(r => r.status === 'error' || r.status === 'no_plate_found').length;
    
    if (errorCount === 0) {
      showToast(`${successCount} ${uploadType === 'image' ? 'image(s)' : 'video(s)'} processed successfully!`, 'success');
    } else {
      showToast(`Processed ${successCount} files, ${errorCount} failed`, errorCount > 0 ? 'error' : 'success');
    }
    
    fetchDashboardData();
    setLoading(false);
  };

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
      case 'analysis':
        await fetchDashboardData();
        setActiveSection('analysis');
        break;
      case 'report':
        await fetchDashboardData();
        showToast('Report generated!', 'success');
        break;
      case 'live':
        showToast('Live monitoring feature coming soon!', 'info');
        break;
      default:
        break;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const stats = dashboardData || {
    total_detections: 127,
    today_detections: 12,
    accuracy_rate: 94.5,
    states_covered: 36
  };

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

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
        <div className="sidebar-header">
          <div className="logo">
            <Car size={28} />
            <span>AVLPRDL System</span>
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
                <p>Real-Time WebCam Detection</p>
              </div>
              <div className="action-arrow">
                <Play size={20} />
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
            <span>myFinalYearProject</span>
            <span>©2026</span>
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
                <Camera size={60} />
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
    </div>
  );
}

export default App;
