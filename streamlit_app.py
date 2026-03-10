"""
ALPR & Data Logging System - Streamlit Web Application
Automated Vehicle License Plate Recognition (ALPR) & Data Logging

Developer: Uwagboi Andrew Chukwuyem
Matric No: 2203030127
Department: Computer Science
Year: 2026
"""

import streamlit as st
import pandas as pd
import os
import sys
import subprocess
import shutil
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# Page Configuration
st.set_page_config(
    page_title="ALPR System",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIGURATION ---
LOG_FILES = {
    "Batch": "batch_log.xlsx",
    "Video": "video_log.xlsx",
    "Live": "live_log.xlsx"
}

EVIDENCE_FOLDER = "test_results/evidence_plates"

# --- CSS STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 50px;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    .metric-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def load_logs():
    """Load and combine all log files"""
    all_data = []
    for name, filepath in LOG_FILES.items():
        if os.path.exists(filepath):
            try:
                df = pd.read_excel(filepath)
                df['Source'] = name
                all_data.append(df)
            except Exception as e:
                st.error(f"Error reading {filepath}: {e}")
    
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()

def get_analytics(df):
    """Calculate analytics from the data"""
    if df.empty:
        return {
            'total_detections': 0,
            'unique_plates': 0,
            'top_state': 'N/A',
            'total_batches': 0
        }
    
    # Count unique plates
    if 'Plate_Number' in df.columns:
        unique_plates = df['Plate_Number'].nunique()
    else:
        unique_plates = 0
    
    # Get top state
    top_state = 'N/A'
    if 'Origin_Capital' in df.columns:
        valid_states = df[df['Origin_Capital'] != 'Unknown']
        if not valid_states.empty:
            top_state = valid_states['Origin_Capital'].value_counts().idxmax()
    
    return {
        'total_detections': len(df),
        'unique_plates': unique_plates,
        'top_state': top_state,
        'total_batches': df['Source'].nunique() if 'Source' in df.columns else 0
    }

def run_script(script_name, *args):
    """Run a Python script and return the result"""
    cmd = [sys.executable, script_name]
    cmd.extend(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Script timed out"
    except Exception as e:
        return False, "", str(e)

def archive_logs():
    """Archive existing logs and create fresh ones"""
    archive_dir = "Archived_Logs"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for name, filepath in LOG_FILES.items():
        if os.path.exists(filepath):
            archive_path = os.path.join(archive_dir, f"{name}_{timestamp}.xlsx")
            shutil.move(filepath, archive_path)
    
    return timestamp

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚗 ALPR System")
    st.markdown("---")
    
    menu = st.radio(
        "Navigation",
        ["Dashboard", "Process Images", "Process Video", "Analytics", "Settings"]
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.info("""
    **ALPR System v1.0**
    
    Automated Vehicle License Plate Recognition & Data Logging
    
    Developed for Final Year Project (2026)
    """)

# --- MAIN CONTENT ---
if menu == "Dashboard":
    st.title("📊 ALPR Dashboard")
    st.markdown("### Real-Time Detection & Intelligent Data Archiving")
    
    # Load data
    df = load_logs()
    analytics = get_analytics(df)
    
    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Detections", analytics['total_detections'])
    
    with col2:
        st.metric("Unique Plates", analytics['unique_plates'])
    
    with col3:
        st.metric("Top State/Capital", analytics['top_state'])
    
    with col4:
        st.metric("Data Sources", analytics['total_batches'])
    
    st.markdown("---")
    
    # Recent detections
    st.subheader("Recent Detections")
    
    if not df.empty:
        # Display most recent 10 detections
        display_df = df.tail(10)
        
        # Format for display
        if 'Plate_Number' in display_df.columns:
            cols_to_show = ['Plate_Number']
            if 'Origin_Capital' in display_df.columns:
                cols_to_show.append('Origin_Capital')
            if 'Source' in display_df.columns:
                cols_to_show.append('Source')
            
            st.dataframe(display_df[cols_to_show], use_container_width=True)
            
            # Show evidence images if available
            if 'Plate_Number' in df.columns:
                st.markdown("### Recent Plate Evidence")
                recent_plates = df['Plate_Number'].dropna().unique()[-6:]
                
                cols = st.columns(3)
                for i, plate in enumerate(recent_plates):
                    # Find evidence file
                    safe_name = ''.join(c for c in str(plate) if c.isalnum())
                    evidence_files = [f for f in os.listdir(EVIDENCE_FOLDER) if safe_name in f]
                    
                    if evidence_files:
                        with cols[i % 3]:
                            img_path = os.path.join(EVIDENCE_FOLDER, evidence_files[0])
                            st.image(img_path, caption=str(plate), use_container_width=True)
    else:
        st.info("No detections yet. Go to 'Process Images' or 'Process Video' to start detecting!")
    
    # Quick actions
    st.markdown("---")
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📂 Process Images", use_container_width=True):
            st.switch_page("?menu=Process Images")
    
    with col2:
        if st.button("📺 Process Video", use_container_width=True):
            st.switch_page("?menu=Process Video")
    
    with col3:
        if st.button("📈 View Analytics", use_container_width=True):
            st.switch_page("?menu=Analytics")


elif menu == "Process Images":
    st.title("📂 Process Image Dataset")
    
    st.markdown("""
    Upload or select a folder of images to process.
    The system will detect and recognize license plates from Nigerian vehicles.
    """)
    
    # Option to use default test images
    use_default = st.checkbox("Use default test images folder", value=True)
    
    if use_default:
        st.info(f"Using default folder: `test_images`")
        input_folder = "test_images"
        
        if os.path.exists(input_folder):
            images = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            st.write(f"Found {len(images)} images in the folder")
            
            if st.button("🚀 Start Batch Processing", type="primary"):
                with st.spinner("Processing images... This may take a while..."):
                    success, stdout, stderr = run_script("batch_test.py")
                    
                    if success:
                        st.success("✅ Processing completed successfully!")
                        st.markdown("### Results")
                        
                        # Load and display results
                        if os.path.exists("batch_log.xlsx"):
                            results_df = pd.read_excel("batch_log.xlsx")
                            st.dataframe(results_df, use_container_width=True)
                    else:
                        st.error(f"❌ Error: {stderr}")
        else:
            st.error(f"Folder '{input_folder}' not found!")
    
    # Custom folder option
    if not use_default:
        custom_folder = st.text_input("Enter folder path:")
        
        if custom_folder and os.path.exists(custom_folder):
            images = [f for f in os.listdir(custom_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            st.write(f"Found {len(images)} images")
            
            if st.button("🚀 Process Custom Folder", type="primary"):
                with st.spinner("Processing images..."):
                    success, stdout, stderr = run_script("batch_test.py", custom_folder)
                    
                    if success:
                        st.success("✅ Processing completed!")
                    else:
                        st.error(f"❌ Error: {stderr}")


elif menu == "Process Video":
    st.title("📺 Process Video")
    
    st.markdown("""
    Upload or select a video file to analyze.
    The system will detect and track license plates in real-time.
    """)
    
    # Option to use default video
    use_default = st.checkbox("Use default test video", value=True)
    
    if use_default:
        video_path = "video_feed_car_test.mp4"
        
        if os.path.exists(video_path):
            # Display video info
            st.video(video_path)
            
            if st.button("🚀 Analyze Video", type="primary"):
                with st.spinner("Analyzing video... This may take a while..."):
                    success, stdout, stderr = run_script("video_test.py")
                    
                    if success:
                        st.success("✅ Video analysis completed!")
                        st.markdown("### Results")
                        
                        if os.path.exists("video_log.xlsx"):
                            results_df = pd.read_excel("video_log.xlsx")
                            st.dataframe(results_df, use_container_width=True)
                    else:
                        st.error(f"❌ Error: {stderr}")
        else:
            st.error(f"Video file '{video_path}' not found!")
    
    # Custom video option
    if not use_default:
        custom_video = st.text_input("Enter video file path:")
        
        if custom_video and os.path.exists(custom_video):
            st.video(custom_video)
            
            if st.button("🚀 Analyze Custom Video", type="primary"):
                with st.spinner("Analyzing video..."):
                    success, stdout, stderr = run_script("video_test.py", custom_video)
                    
                    if success:
                        st.success("✅ Analysis completed!")
                    else:
                        st.error(f"❌ Error: {stderr}")


elif menu == "Analytics":
    st.title("📈 System Analytics")
    
    # Load all data
    df = load_logs()
    
    if df.empty:
        st.info("No data available for analytics. Process some images or videos first!")
    else:
        # Overview metrics
        analytics = get_analytics(df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Detections", analytics['total_detections'])
            st.metric("Unique Plates", analytics['unique_plates'])
        
        with col2:
            st.metric("Top State/Capital", analytics['top_state'])
            st.metric("Data Sources", analytics['total_batches'])
        
        st.markdown("---")
        
        # State distribution
        if 'Origin_Capital' in df.columns:
            st.subheader("State Distribution")
            
            state_counts = df['Origin_Capital'].value_counts()
            st.bar_chart(state_counts)
        
        # Source breakdown
        if 'Source' in df.columns:
            st.subheader("Detection by Source")
            source_counts = df['Source'].value_counts()
            st.bar_chart(source_counts)
        
        # Confidence levels
        if 'Confidence' in df.columns:
            st.subheader("Detection Confidence")
            st.line_chart(df['Confidence'].tail(50))
        
        # Full data table
        st.markdown("---")
        st.subheader("Full Data")
        
        st.dataframe(df, use_container_width=True)
        
        # Export option
        if st.button("📥 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"alpr_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


elif menu == "Settings":
    st.title("⚙️ Settings")
    
    st.markdown("### Archive & Reset")
    
    st.warning("This will archive all current logs and create fresh ones.")
    
    if st.button("🧹 Archive and Reset Logs", type="primary"):
        timestamp = archive_logs()
        st.success(f"Logs archived successfully! Timestamp: {timestamp}")
    
    st.markdown("---")
    
    st.markdown("### Log Files")
    
    for name, filepath in LOG_FILES.items():
        if os.path.exists(filepath):
            try:
                df = pd.read_excel(filepath)
                st.write(f"**{name}**: {len(df)} records")
            except:
                st.write(f"**{name}**: Unable to read")
        else:
            st.write(f"**{name}**: Not found")
    
    st.markdown("---")
    
    st.markdown("### System Information")
    
    st.markdown(f"""
    - **Python Version**: {sys.version.split()[0]}
    - **Working Directory**: {os.getcwd()}
    - **Evidence Folder**: {EVIDENCE_FOLDER}
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Developed for Final Year Project (2026) | ALPR & Data Logging System"
    "</div>",
    unsafe_allow_html=True
)
