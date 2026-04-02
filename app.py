import streamlit as st
import requests
import pandas as pd
import cv2
import plotly.express as px
import os
import time

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Temple Crowd Dashboard",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.title("🛕 AI-Based Temple Crowd Management System")

# -----------------------------
# READ QUERY PARAM (FROM FRONTEND BUTTON)
# -----------------------------
query_params = st.query_params
current_page = query_params.get("page", "dashboard")

# Map page names to view names for backward compatibility
page_to_view = {
    "dashboard": "dashboard",
    "monitoring": "live",
    "heatmap": "heatmap",
    "analytics": "analytics",
    "threshold": "thresholds",
}

current_view = page_to_view.get(current_page, "dashboard")

# -----------------------------
# SIDEBAR NAVIGATION
# -----------------------------
with st.sidebar:
    st.header("📋 Navigation")
    view_options = {
        "Dashboard": "dashboard",
        "Live Monitoring": "live",
        "Zone Monitoring": "zones",
        "Heatmap": "heatmap",
        "Waiting Time": "waiting",
        "Analytics": "analytics",
        "⚙️ Threshold Settings": "thresholds"
    }
    
    # Find current index
    current_index = 0
    if current_view in view_options.values():
        current_index = list(view_options.values()).index(current_view)
    
    selected_view = st.radio(
        "Select View",
        options=list(view_options.keys()),
        index=current_index
    )
    
    # Update query params based on selection
    if st.button("Go"):
        st.query_params["view"] = view_options[selected_view]
        st.rerun()

st.markdown("---")


# -----------------------------
# BACKEND API
# -----------------------------
API_BASE = "http://localhost:5001"  # Flask backend port

backend_ok = True

try:
    live_counts = requests.get(
        f"{API_BASE}/live_counts", timeout=2
    ).json()
except Exception as e:
    backend_ok = False
    live_counts = {
        "Entrance": 0,
        "Queue": 0,
        "Sanctum": 0,
        "Exit": 0
    }

try:
    history = requests.get(
        f"{API_BASE}/history", timeout=2
    ).json()
except Exception as e:
    history = []

# --- NEW: FETCH AUDIO STATUS ---
try:
    status_data = requests.get(f"{API_BASE}/status", timeout=2).json()
    audio_alert_active = status_data.get("audio_alert", False)
except Exception as e:
    audio_alert_active = False
# -------------------------------

if backend_ok:
    st.success("Backend connected ✅ Live data")
else:
    st.warning("Backend not connected. Showing demo data.")



total_crowd = sum(live_counts.values())
queue_count = live_counts.get("Queue", 0)

# -----------------------------
# TOP SUMMARY (ALWAYS SHOWN)
# -----------------------------

if audio_alert_active:
    st.error("🚨 **BLINDSPOT AI TRIGGERED: Loud Panic/Screaming Detected!** 🚨 \n\n Check CCTV and deploy personnel immediately.", icon="🚨")

col1, col2, col3 = st.columns(3)

col1.metric("👥 Total Crowd", total_crowd)

AVG_TIME_PER_PERSON = 5
wait_time_min = round((queue_count * AVG_TIME_PER_PERSON) / 60, 2)
col2.metric("🕒 Est. Time to Reach God (min)", wait_time_min)

if total_crowd < 15:
    col3.success("🟢 Status: Safe")
elif total_crowd < 20:
    col3.warning("🟡 Status: Warning")
else:
    col3.error("🔴 Status: Critical")

st.markdown("---")

# =================================================
# 1️⃣ LIVE CROWD MONITORING
# =================================================
if current_view in ["dashboard", "live"]:
    st.header("🎥 Live Crowd Monitoring")

    cols = st.columns(len(live_counts))

    for col, (cam, count) in zip(cols, live_counts.items()):
        col.subheader(cam)
        col.metric("Head Count", count)

        zone_key = cam.lower()
        frame_path = os.path.join(BASE_DIR, f"latest_frame_{zone_key}.jpg")
        
        # Check if frame file exists and is readable
        if os.path.exists(frame_path):
            try:
                frame = cv2.imread(frame_path)
                if frame is not None and frame.size > 0:
                    # Convert BGR to RGB for display
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    col.image(frame_rgb, use_container_width=True, caption=f"Live feed: {cam}")
                else:
                    col.warning(f"⚠️ Frame file exists but couldn't be read for {cam}")
            except Exception as e:
                col.error(f"❌ Error loading frame for {cam}: {str(e)}")
        else:
            col.info(f"⏳ Waiting for feed from {cam}...")

#-----------------------------------------

    time.sleep(2) # Wait 2 seconds
    st.rerun()

# =================================================
# 2️⃣ ZONE-WISE MONITORING
# =================================================
if current_view in ["dashboard", "zones"]:
    st.markdown("---")
    st.header("🚪 Zone-wise Crowd Monitoring")

    zone_data = {
        "Entrance": live_counts.get("Entrance", 0),
        "Queue": queue_count,
        "Sanctum": live_counts.get("Sanctum", 0),
        "Exit": live_counts.get("Exit", 0)
    }

    zone_cols = st.columns(4)
    for col, (zone, count) in zip(zone_cols, zone_data.items()):
        col.metric(zone, count)

# =================================================
# 3️⃣ HEATMAP VIEW
# =================================================
if current_view in ["dashboard", "heatmap"]:
    st.markdown("---")
    st.header("🔥 Crowd Density Heatmap")

    heatmap_path = os.path.join(BASE_DIR, "latest_heatmap.jpg")
    heatmap = cv2.imread(heatmap_path)

    if heatmap is not None:
        st.image(heatmap, channels="BGR", use_container_width=True)
    else:
        st.info("Heatmap loading...")

# =================================================
# 4️⃣ WAITING TIME ESTIMATION
# =================================================
if current_view in ["dashboard", "waiting"]:
    st.markdown("---")
    st.header("🕒 Estimated Waiting Time")

    if wait_time_min < 5:
        st.success(f"Approx. Waiting Time: {wait_time_min} minutes")
    elif wait_time_min < 15:
        st.warning(f"Approx. Waiting Time: {wait_time_min} minutes")
    else:
        st.error(f"Approx. Waiting Time: {wait_time_min} minutes")

# =================================================
# 5️⃣ CROWD ANALYTICS
# =================================================
if current_view in ["dashboard", "analytics"]:
    st.markdown("---")
    st.header("📈 Crowd Analytics & Trends")

    import pandas as pd
    import numpy as np
    import datetime

    # Generate demo data
    time_range = pd.date_range(end=datetime.datetime.now(), periods=30, freq="1min")
    crowd_counts = np.random.randint(20, 120, size=30)

    df = pd.DataFrame({
        "timestamp": time_range,
        "count": crowd_counts
    })

    # 1️⃣ Line Graph
    fig = px.line(
        df,
        x="timestamp",
        y="count",
        title="Crowd Count Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)

    
    


# =================================================
# 6️⃣ THRESHOLD CONFIGURATION
# =================================================

def _show_threshold_form(current_thresholds, error_type="normal"):
    """Helper function to display threshold configuration form"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Total Crowd Threshold")
        total_threshold = st.number_input(
            "Maximum Total Crowd Count",
            min_value=0,
            max_value=1000,
            value=current_thresholds.get("total_crowd", 20),
            key=f"total_threshold_{error_type}",
            help="Alert when total crowd across all zones exceeds this number"
        )
        # --- NEW: AUDIO SENSITIVITY SLIDER ---
        st.markdown("---")
        st.subheader("🎙️ Audio Panic Detection")
        audio_threshold = st.slider(
            "Sound Detection Limit (Volume)",
            min_value=50,
            max_value=500,
            value=current_thresholds.get("audio_threshold", 150),
            step=10,
            key=f"audio_threshold_{error_type}",
            help="Lower = More sensitive to noise. Higher = Requires very loud noises to trigger."
        )
    
    with col2:
        st.subheader("Zone-Specific Thresholds")
        zone_thresholds = {}
        zones_data = current_thresholds.get("zones", {})
        
        zone_thresholds["Entrance"] = st.number_input(
            "Entrance Zone",
            min_value=0,
            max_value=500,
            value=zones_data.get("Entrance", 10),
            key=f"entrance_threshold_{error_type}"
        )
        
        zone_thresholds["Queue"] = st.number_input(
            "Queue Zone",
            min_value=0,
            max_value=500,
            value=zones_data.get("Queue", 15),
            key=f"queue_threshold_{error_type}"
        )
        
        zone_thresholds["Sanctum"] = st.number_input(
            "Sanctum Zone",
            min_value=0,
            max_value=500,
            value=zones_data.get("Sanctum", 8),
            key=f"sanctum_threshold_{error_type}"
        )
        
        zone_thresholds["Exit"] = st.number_input(
            "Exit Zone",
            min_value=0,
            max_value=500,
            value=zones_data.get("Exit", 10),
            key=f"exit_threshold_{error_type}"
        )
    
    # Save button
    if st.button("💾 Save Thresholds", type="primary", use_container_width=True, key=f"save_{error_type}"):
        try:
            update_response = requests.post(
                f"{API_BASE}/thresholds",
                json={
                    "total_crowd": total_threshold,
                    "zones": zone_thresholds,
                    "audio_threshold": audio_threshold # --- NEW: SEND TO BACKEND ---
                },
                timeout=10
            )
            
            if update_response.status_code == 200:
                st.success("✅ Thresholds updated successfully!")
                st.rerun()
            else:
                error_msg = update_response.json().get("error", "Unknown error")
                st.error(f"❌ Failed to update thresholds: {error_msg}")
        except Exception as e:
            st.error(f"❌ Error updating thresholds: {str(e)}")
            st.info("Please make sure the backend server is running: `python yolo_processor_mongo.py`")
    
    # Display current values
    st.markdown("### 📊 Current Threshold Values")
    threshold_cols = st.columns(6)
    threshold_cols[0].metric("Total Crowd", total_threshold)
    threshold_cols[1].metric("Entrance", zone_thresholds["Entrance"])
    threshold_cols[2].metric("Queue", zone_thresholds["Queue"])
    threshold_cols[3].metric("Sanctum", zone_thresholds["Sanctum"])
    threshold_cols[4].metric("Exit", zone_thresholds["Exit"])
    threshold_cols[5].metric("Audio Limit", audio_threshold)


if current_view in ["dashboard", "settings", "thresholds"]:
    st.markdown("---")
    st.header("⚙️ Threshold Configuration")
    st.info("Configure alert thresholds. Changes are saved automatically and take effect immediately.")

    try:
        # Get current thresholds with longer timeout
        thresholds_response = requests.get(f"{API_BASE}/thresholds", timeout=10)
        if thresholds_response.status_code == 200:
            current_thresholds = thresholds_response.json()
            _show_threshold_form(current_thresholds, "normal")
        else:
            st.warning("⚠️ Could not load current thresholds. Please check backend connection.")
            st.info("💡 Using default threshold values. You can still update them below.")
            current_thresholds = {
                "total_crowd": 20,
                "zones": {
                    "Entrance": 10,
                    "Queue": 15,
                    "Sanctum": 8,
                    "Exit": 10
                }
            }
            _show_threshold_form(current_thresholds, "fallback")
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. The backend server may be slow or not responding.")
        st.info("💡 You can still configure thresholds - they will be saved when the backend is available.")
        # Show form with defaults
        current_thresholds = {
            "total_crowd": 20,
            "zones": {"Entrance": 10, "Queue": 15, "Sanctum": 8, "Exit": 10}
        }
        _show_threshold_form(current_thresholds, "timeout")
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot connect to backend server.")
        st.info("💡 Please start the backend server: `python yolo_processor_mongo.py`")
        # Show form with defaults
        current_thresholds = {
            "total_crowd": 20,
            "zones": {"Entrance": 10, "Queue": 15, "Sanctum": 8, "Exit": 10}
        }
        _show_threshold_form(current_thresholds, "connection_error")
    except Exception as e:
        st.error(f"❌ Error loading thresholds: {str(e)}")
        st.info("💡 You can still configure thresholds below - they will be saved when the backend is available.")
        # Show form with defaults
        current_thresholds = {
            "total_crowd": 20,
            "zones": {"Entrance": 10, "Queue": 15, "Sanctum": 8, "Exit": 10}
        }
        _show_threshold_form(current_thresholds, "error")

