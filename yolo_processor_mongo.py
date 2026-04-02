from flask import Flask, jsonify, request, Response
from pymongo import MongoClient
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import threading
import time
import cv2
import os
import numpy as np
from ultralytics import YOLO
import requests
import json
import sqlite3
import hashlib
import sounddevice as sd
import urllib.request


# Try to import flask-cors for CORS support
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("ℹ️  flask-cors not installed. CORS headers will be set manually.")

# Try to load .env file if python-dotenv is installed
# Testing 
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("ℹ️  python-dotenv not installed. Using system environment variables.")

# ----------------------------------
# BASIC SETUP
# ----------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# Enable CORS for frontend requests
if CORS_AVAILABLE:
    CORS(app)
else:
    # Manual CORS headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # Handle OPTIONS requests for CORS preflight
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
            response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
            return response

# ----------------------------------
# SQLITE AUTHENTICATION DATABASE
# ----------------------------------
AUTH_DB_PATH = os.path.join(BASE_DIR, "auth.db")

def init_auth_db():
    """Initialize SQLite authentication database"""
    conn = sqlite3.connect(AUTH_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('operator', 'admin'))
        )
    ''')
    conn.commit()
    
    # Create default users if table is empty
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        # Default credentials: operator/operator123, admin/admin123
        default_users = [
            ('operator', hashlib.sha256('operator123'.encode()).hexdigest(), 'operator'),
            ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin'),
        ]
        cursor.executemany(
            'INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
            default_users
        )
        conn.commit()
        print("✅ Created default users: operator/operator123, admin/admin123")
    
    conn.close()

# Initialize auth database on startup
init_auth_db()

# ----------------------------------
# MONGODB ATLAS CONNECTION
# ----------------------------------
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB connection with error handling
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
    # Test connection
    client.admin.command('ping')
    db = client["temple_crowd_db"]
    collection = db["crowd_data"]
    thresholds_collection = db["thresholds"]  # Store threshold configurations
    print("✅ MongoDB connected successfully")
    mongo_connected = True
except Exception as e:
    print(f"⚠️  MongoDB connection failed: {str(e)}")
    print("⚠️  Continuing without MongoDB - data will not be persisted")
    client = None
    db = None
    collection = None
    thresholds_collection = None
    mongo_connected = False

# ----------------------------------
# LOAD YOLO MODEL
# ----------------------------------
model = YOLO("yolov8n.pt")

# ----------------------------------
# LIVE VIDEO SOURCES (4 ZONES)
# ----------------------------------
# Each source can be:
# - A webcam index (0, 1, 2, ...) – typically for USB / built‑in webcams
# - An IP camera URL (RTSP/HTTP/MJPEG), e.g. "rtsp://user:pass@ip:554/stream"
#
# Configure via environment variables if needed:
#   ENTRANCE_SOURCE, QUEUE_SOURCE, SANCTUM_SOURCE, EXIT_SOURCE
#
# Defaults below assume multiple webcams connected.
VIDEO_SOURCES = {
    "Entrance": os.getenv("ENTRANCE_SOURCE", "0"),
    "Queue": os.getenv("QUEUE_SOURCE", "1"),
    "Sanctum": os.getenv("SANCTUM_SOURCE", "2"),
    "Exit": os.getenv("EXIT_SOURCE", "3"),
}

# Initialize live video captures with error handling
# Separate captures for streaming (fast) and YOLO (slow)
streaming_caps = {}  # Fast raw video streaming
yolo_caps = {}      # YOLO detection (can be slower)

def open_camera(zone, src):
    """Helper to open a camera source"""
    cap = None
    src_desc = src
    try:
        src_index = int(src)
        cap = cv2.VideoCapture(src_index)
        src_desc = f"camera index {src_index}"
    except ValueError:
        # Not an int → treat as URL/string source
        cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap, src_desc

# Open cameras for streaming (fast pipeline)
for zone, src in VIDEO_SOURCES.items():
    cap, src_desc = open_camera(zone, src)
    if cap is not None and cap.isOpened():
        streaming_caps[zone] = cap
        print(f"✅ Opened streaming camera for {zone}: {src_desc}")
    else:
        print(f"❌ Failed to open streaming camera for {zone}: {src_desc}")

# Open cameras for YOLO (can be same or separate)
for zone, src in VIDEO_SOURCES.items():
    cap, src_desc = open_camera(zone, src)
    if cap is not None and cap.isOpened():
        yolo_caps[zone] = cap
        print(f"✅ Opened YOLO camera for {zone}: {src_desc}")
    else:
        print(f"❌ Failed to open YOLO camera for {zone}: {src_desc}")

# Thread-safe crowd counts
latest_counts = {zone: 0 for zone in VIDEO_SOURCES}
counts_lock = threading.Lock()  # Lock for thread-safe access to latest_counts

# ----------------------------------
# SMS/PHONE NOTIFICATION CONFIGURATION
# ----------------------------------
# Option 1: Using Twilio (Recommended)
# Get these from https://www.twilio.com/console
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")  # Format: +1234567890
RECIPIENT_PHONE_NUMBERS = os.getenv("RECIPIENT_PHONE_NUMBERS", "").split(",")  # Comma-separated, format: +1234567890

# Option 2: Using SMS API (Alternative - like TextBelt, etc.)
SMS_API_URL = os.getenv("SMS_API_URL", "")
SMS_API_KEY = os.getenv("SMS_API_KEY", "")

# Threshold Configuration - Load from MongoDB or use defaults
def load_thresholds():
    """Load thresholds from MongoDB, local file, or use environment variables/defaults"""
    global mongo_connected
    
    # Try MongoDB first
    if mongo_connected is True and thresholds_collection is not None:
        try:
            threshold_doc = thresholds_collection.find_one({"type": "current"})
            if threshold_doc:
                print("✅ Loaded thresholds from MongoDB")
                return {
                    "total_crowd": threshold_doc.get("total_crowd", 20),
                    "zones": threshold_doc.get("zones", {
                        "Entrance": 10,
                        "Queue": 15,
                        "Sanctum": 8,
                        "Exit": 10
                    })
                }
        except Exception as e:
            print(f"⚠️  Could not load thresholds from MongoDB: {e}")
            mongo_connected = False
    
    # Fallback: Try local JSON file
    try:
        thresholds_file = os.path.join(BASE_DIR, "thresholds.json")
        if os.path.exists(thresholds_file):
            with open(thresholds_file, 'r') as f:
                thresholds_data = json.load(f)
            print(f"✅ Loaded thresholds from local file: {thresholds_file}")
            return {
                "total_crowd": thresholds_data.get("total_crowd", 20),
                "zones": thresholds_data.get("zones", {
                    "Entrance": 10,
                    "Queue": 15,
                    "Sanctum": 8,
                    "Exit": 10
                })
            }
    except Exception as e:
        print(f"⚠️  Could not load thresholds from file: {e}")
    
    # Final fallback: Environment variables or defaults
    print("ℹ️  Using default thresholds (from env vars or hardcoded defaults)")
    return {
        "total_crowd": int(os.getenv("THRESHOLD_TOTAL_CROWD", "20")),
        "zones": {
            "Entrance": int(os.getenv("THRESHOLD_ENTRANCE", "10")),
            "Queue": int(os.getenv("THRESHOLD_QUEUE", "15")),
            "Sanctum": int(os.getenv("THRESHOLD_SANCTUM", "8")),
            "Exit": int(os.getenv("THRESHOLD_EXIT", "10"))
        }
    }

def reconnect_mongodb():
    """Attempt to reconnect to MongoDB"""
    global mongo_connected, client, db, collection, thresholds_collection
    
    if mongo_connected:
        return True
    
    try:
        print("🔄 Attempting to reconnect to MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
        client.admin.command('ping')
        db = client["temple_crowd_db"]
        collection = db["crowd_data"]
        thresholds_collection = db["thresholds"]
        mongo_connected = True
        print("✅ MongoDB reconnected successfully")
        return True
    except Exception as e:
        print(f"⚠️  MongoDB reconnection failed: {str(e)}")
        return False

def save_thresholds(total_crowd, zones):
    """Save thresholds to MongoDB or local JSON file as fallback"""
    global mongo_connected
    
    # Try to reconnect if not connected
    if not mongo_connected:
        reconnect_mongodb()
    
    # Try MongoDB first
    if mongo_connected is True and thresholds_collection is not None:
        try:
            result = thresholds_collection.update_one(
                {"type": "current"},
                {
                    "$set": {
                        "total_crowd": total_crowd,
                        "zones": zones,
                        "updated_at": datetime.now()
                    }
                },
                upsert=True
            )
            print(f"✅ Thresholds saved to MongoDB (matched: {result.matched_count}, modified: {result.modified_count})")
            return True
        except Exception as e:
            print(f"⚠️  Error saving to MongoDB: {e}")
            print(f"   Error type: {type(e).__name__}")
            mongo_connected = False
            # Try to reconnect for next time
            reconnect_mongodb()
    
    # Fallback: Save to local JSON file
    try:
        thresholds_file = os.path.join(BASE_DIR, "thresholds.json")
        thresholds_data = {
            "total_crowd": total_crowd,
            "zones": zones,
            "updated_at": datetime.now().isoformat()
        }
        with open(thresholds_file, 'w') as f:
            json.dump(thresholds_data, f, indent=2)
        print(f"✅ Thresholds saved to local file: {thresholds_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving thresholds to file: {e}")
        return False

# Initialize thresholds
thresholds = load_thresholds()
THRESHOLD_TOTAL_CROWD = thresholds["total_crowd"]
THRESHOLD_ZONE_SPECIFIC = thresholds["zones"]

# Alert tracking to prevent spam (send alert max once per 5 minutes)
last_alert_time = {}
ALERT_COOLDOWN_MINUTES = 5

# ----------------------------------
# SMS NOTIFICATION FUNCTIONS
# ----------------------------------
def send_sms_twilio(to_number, message):
    """Send SMS using Twilio API"""
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
            print("⚠️  Twilio credentials not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER")
            return False
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
        payload = {
            "From": TWILIO_PHONE_NUMBER,
            "To": to_number.strip(),
            "Body": message
        }
        response = requests.post(url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), data=payload)
        
        if response.status_code == 201:
            print(f"✅ SMS sent successfully to {to_number}")
            return True
        else:
            print(f"❌ Failed to send SMS: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending SMS via Twilio: {str(e)}")
        return False

def send_sms_api(to_number, message):
    """Send SMS using generic SMS API"""
    try:
        if not SMS_API_URL or not SMS_API_KEY:
            print("⚠️  SMS API credentials not configured")
            return False
        
        payload = {
            "api_key": SMS_API_KEY,
            "to": to_number.strip(),
            "message": message
        }
        response = requests.post(SMS_API_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ SMS sent successfully to {to_number}")
            return True
        else:
            print(f"❌ Failed to send SMS: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending SMS via API: {str(e)}")
        return False

def send_sms_notification(to_numbers, message):
    """Send SMS to multiple recipients"""
    success_count = 0
    for number in to_numbers:
        if number.strip():
            if TWILIO_ACCOUNT_SID:
                if send_sms_twilio(number, message):
                    success_count += 1
            elif SMS_API_URL:
                if send_sms_api(number, message):
                    success_count += 1
            else:
                print("⚠️  No SMS service configured. Please set up Twilio or SMS API credentials")
                return False
    return success_count > 0

def check_threshold_and_alert(counts):
    """Check if thresholds are exceeded and send alerts"""
    global last_alert_time, THRESHOLD_TOTAL_CROWD, THRESHOLD_ZONE_SPECIFIC
    
    # Use current global variables (which are updated immediately when user changes thresholds)
    # Only reload from storage if globals are not set (shouldn't happen, but safety check)
    if THRESHOLD_TOTAL_CROWD is None or not THRESHOLD_ZONE_SPECIFIC:
        thresholds = load_thresholds()
        THRESHOLD_TOTAL_CROWD = thresholds["total_crowd"]
        THRESHOLD_ZONE_SPECIFIC = thresholds["zones"]
    
    # Use the global variables directly (they're updated immediately when thresholds change)
    # This ensures alerts use the latest thresholds without delay
    
    current_time = datetime.now()
    total_crowd = sum(counts.values())
    
    alerts_to_send = []
    
    # Check total crowd threshold
    if total_crowd >= THRESHOLD_TOTAL_CROWD:
        alert_key = "total_crowd"
        if alert_key not in last_alert_time or \
           (current_time - last_alert_time[alert_key]) > timedelta(minutes=ALERT_COOLDOWN_MINUTES):
            alerts_to_send.append({
                "type": "Total Crowd",
                "count": total_crowd,
                "threshold": THRESHOLD_TOTAL_CROWD,
                "message": f"🚨 ALERT: Total crowd count ({total_crowd}) exceeded threshold ({THRESHOLD_TOTAL_CROWD})!\n\nZone breakdown:\n" + 
                           "\n".join([f"{zone}: {count} heads" for zone, count in counts.items()])
            })
            last_alert_time[alert_key] = current_time
    
    # Check zone-specific thresholds
    for zone, count in counts.items():
        threshold = THRESHOLD_ZONE_SPECIFIC.get(zone, 10)
        if count >= threshold:
            alert_key = f"zone_{zone}"
            if alert_key not in last_alert_time or \
               (current_time - last_alert_time[alert_key]) > timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                alerts_to_send.append({
                    "type": f"{zone} Zone",
                    "count": count,
                    "threshold": threshold,
                    "message": f"🚨 ALERT: {zone} zone crowd count ({count} heads) exceeded threshold ({threshold})!\n\nTotal crowd: {total_crowd} heads"
                })
                last_alert_time[alert_key] = current_time
    
    # Send alerts
    if alerts_to_send and RECIPIENT_PHONE_NUMBERS:
        for alert in alerts_to_send:
            print(f"📱 Sending alert: {alert['type']} - Count: {alert['count']}, Threshold: {alert['threshold']}")
            send_sms_notification(RECIPIENT_PHONE_NUMBERS, alert['message'])
    elif alerts_to_send:
        print(f"⚠️  Alert triggered but no recipient phone numbers configured")
        print(f"   Alert: {alerts_to_send[0]['type']} - Count: {alerts_to_send[0]['count']}, Threshold: {alerts_to_send[0]['threshold']}")

# ----------------------------------
# HEAD DETECTION FUNCTION
# ----------------------------------
def detect_heads_in_frame(frame, person_boxes):
    """
    Detect heads within person bounding boxes.
    Uses the upper portion of person boxes and additional validation.
    """
    head_detections = []
    
    for x1, y1, x2, y2 in person_boxes:
        # Extract person bounding box
        person_height = y2 - y1
        person_width = x2 - x1
        
        # Head is typically in the upper 1/3 to 1/4 of person box
        head_region_height = int(person_height * 0.35)  # Upper 35% for head
        head_y1 = y1
        head_y2 = y1 + head_region_height
        
        # Head width is typically 60-80% of person width, centered
        head_width_ratio = 0.7
        head_width = int(person_width * head_width_ratio)
        head_x_offset = int(person_width * (1 - head_width_ratio) / 2)
        head_x1 = x1 + head_x_offset
        head_x2 = head_x1 + head_width
        
        # Ensure coordinates are within frame bounds
        head_x1 = max(0, head_x1)
        head_y1 = max(0, head_y1)
        head_x2 = min(frame.shape[1], head_x2)
        head_y2 = min(frame.shape[0], head_y2)
        
        # Calculate head center
        head_cx = (head_x1 + head_x2) // 2
        head_cy = (head_y1 + head_y2) // 2
        
        # Validate head region (minimum size check)
        if (head_x2 - head_x1) > 10 and (head_y2 - head_y1) > 10:
            head_detections.append({
                'box': (head_x1, head_y1, head_x2, head_y2),
                'center': (head_cx, head_cy)
            })
    
    return head_detections

def refine_head_detection_with_hog(frame, head_regions, zone=None):
    """
    Refine head detection using edge detection validation.
    This helps filter out false positives.
    """
    refined_heads = []
    
    # Lower threshold for exit zone (might have different lighting/conditions)
    edge_threshold = 0.03 if zone == "Exit" else 0.05
    
    for head_info in head_regions:
        x1, y1, x2, y2 = head_info['box']
        head_roi = frame[y1:y2, x1:x2]
        
        if head_roi.size > 0:
            # Resize ROI for better edge detection
            roi_h, roi_w = head_roi.shape[:2]
            if roi_h > 20 and roi_w > 20:  # Minimum size check
                # Simple validation: check if region has sufficient detail
                gray = cv2.cvtColor(head_roi, cv2.COLOR_BGR2GRAY) if len(head_roi.shape) == 3 else head_roi
                
                # Use adaptive threshold for better edge detection
                edges = cv2.Canny(gray, 30, 100)
                edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
                
                # Also check variance (texture) - heads usually have some texture
                variance = np.var(gray)
                
                # If edge density is reasonable OR variance is high, consider it a valid head
                if edge_density > edge_threshold or variance > 100:
                    refined_heads.append(head_info)
            else:
                # Very small regions - likely valid heads (close-up)
                refined_heads.append(head_info)
    
    # Always return at least the original detections if refinement is too strict
    return refined_heads if refined_heads else head_regions

# ----------------------------------
# HEATMAP FUNCTION
# ----------------------------------
def generate_yolo_heatmap(detections, frame_shape):
    heatmap = np.zeros(frame_shape[:2], dtype=np.float32)

    height, width = frame_shape[:2]

    for (cx, cy) in detections:
        cx = max(0, min(cx, width - 1))
        cy = max(0, min(cy, height - 1))
        heatmap[cy, cx] += 1

    heatmap = cv2.GaussianBlur(heatmap, (0, 0), 25)
    heatmap = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX)
    return cv2.applyColorMap(heatmap.astype(np.uint8), cv2.COLORMAP_JET)

# ----------------------------------
# YOLO CROWD COUNTING LOOP (SLOW PIPELINE)
# Runs in background thread, processes every N frames
# ----------------------------------
YOLO_FRAME_SKIP = 10  # Process every 10th frame (adjust for performance)

def yolo_video_loop():
    """Background thread for YOLO detection - runs independently of video streaming"""
    global latest_counts, mongo_connected
    
    frame_counters = {zone: 0 for zone in VIDEO_SOURCES}

    while True:
        all_centers = []
        last_frame = None

        for zone, cap in yolo_caps.items():
            try:
        # Skip frames for performance
                frame_counters[zone] += 1
                if frame_counters[zone] % YOLO_FRAME_SKIP != 0:
                    continue  # ← also remove cap.grab() here for IP cams
        
                src = VIDEO_SOURCES.get(zone, "0")

        # For IP webcam - fetch snapshot directly
                if isinstance(src, str) and src.startswith("http"):
                    try:
                        snapshot_url = src.replace("/video", "/shot.jpg").replace("/videofeed", "/shot.jpg")
                        with urllib.request.urlopen(snapshot_url, timeout=2) as resp:
                            img_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)
                            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        if frame is None or frame.size == 0:
                            continue
                    except Exception as e:
                        print(f"❌ YOLO snapshot error for {zone}: {e}")
                        continue
                else:
            # For webcam index - read directly
                    cap.grab()
                    ret, frame = cap.read()
                    if not ret:
                        continue
                    if frame is None or frame.size == 0:
                        continue

                last_frame = frame  # Store for heatmap generation

                # 🔹 RUN YOLO DETECTION FOR PERSONS
                if zone == "Exit":
                    print(f"🔍 Exit: Processing frame, shape: {frame.shape}")
                results = model(frame, conf=0.25, verbose=False)

                person_boxes = []
                person_centers = []

                # First pass: detect persons
                for r in results:
                    for box in r.boxes:
                        if int(box.cls[0]) == 0:  # person class
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            person_boxes.append((x1, y1, x2, y2))
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            person_centers.append((cx, cy))
                            # Draw person box (light green)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

                if zone == "Exit":
                    print(f"🔍 Exit: Found {len(person_boxes)} persons")

                # 🔹 DETECT HEADS WITHIN PERSON BOXES
                head_detections = detect_heads_in_frame(frame, person_boxes)
                
                if zone == "Exit":
                    print(f"🔍 Exit: Detected {len(head_detections)} head regions")
                
                # Refine head detections (pass zone for zone-specific thresholds)
                refined_heads = refine_head_detection_with_hog(frame, head_detections, zone=zone)
                
                if zone == "Exit":
                    print(f"🔍 Exit: Refined to {len(refined_heads)} heads")
                
                # Draw head boxes and count
                head_centers = []
                for head_info in refined_heads:
                    hx1, hy1, hx2, hy2 = head_info['box']
                    hcx, hcy = head_info['center']
                    
                    # Draw head box (bright blue/cyan)
                    cv2.rectangle(frame, (hx1, hy1), (hx2, hy2), (255, 255, 0), 2)
                    # Draw head center point
                    cv2.circle(frame, (hcx, hcy), 3, (255, 255, 0), -1)
                    head_centers.append((hcx, hcy))
                    all_centers.append((hcx, hcy))

                # Count heads instead of persons
                head_count = len(refined_heads)
                
                # Thread-safe update of counts
                with counts_lock:
                    latest_counts[zone] = head_count

                # Display head count on frame
                cv2.putText(
                    frame,
                    f"{zone} | Heads: {head_count}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 0),
                    2
                )
                # Also show person count for reference
                cv2.putText(
                    frame,
                    f"Persons: {len(person_boxes)}",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
                
                # Special logging for Entrance and Exit zones
                if zone in ["Entrance", "Exit"]:
                    print(f"🔵 {zone} zone: Detected {head_count} heads (from {len(person_boxes)} persons)")

                # Save frame
                frame_path = os.path.join(BASE_DIR, f"latest_frame_{zone.lower()}.jpg")
                success = cv2.imwrite(frame_path, frame)
                
                if zone == "Exit":
                    print(f"🔴 Exit zone: Detected {head_count} heads (from {len(person_boxes)} persons)")
                    print(f"🔴 Exit: Frame saved: {success}, path: {frame_path}")
                    if head_count == 0 and len(person_boxes) > 0:
                        print(f"⚠️  Exit: WARNING - Found {len(person_boxes)} persons but 0 heads!")

            except Exception as e:
                print(f"❌ Error processing {zone}: {str(e)}")
                continue

        # 🔥 HEATMAP IMAGE (GLOBAL)
        if all_centers and last_frame is not None:
            try:
        # Resize all frames to standard size before heatmap generation
                standard_shape = (480, 640, 3)
                resized_frame = cv2.resize(last_frame, (640, 480))
        
        # Scale detection centers to standard size
                orig_h, orig_w = last_frame.shape[:2]
                scaled_centers = [
                    (int(cx * 640 / orig_w), int(cy * 480 / orig_h))
                    for (cx, cy) in all_centers
                ]
        
                heatmap_img = generate_yolo_heatmap(scaled_centers, standard_shape)
                cv2.imwrite(os.path.join(BASE_DIR, "latest_heatmap.jpg"), heatmap_img)
            except Exception as e:
                print(f"❌ Error generating heatmap: {str(e)}")

        # 🔹 STORE IN MONGODB
        if mongo_connected is True and collection is not None:
            try:
                data = {
                    "timestamp": datetime.now(),
                    "zones": latest_counts.copy(),
                    "count": sum(latest_counts.values())
                }
                collection.insert_one(data)
            except Exception as e:
                print(f"❌ Error storing in MongoDB: {str(e)}")
                # Try to reconnect
                try:
                    client.admin.command('ping')
                    mongo_connected = True
                except:
                    mongo_connected = False
        else:
            # MongoDB not connected - skip storage (app continues to work)
            pass

        # 📱 CHECK THRESHOLDS AND SEND ALERTS (thread-safe read)
        with counts_lock:
            counts_copy = latest_counts.copy()
        check_threshold_and_alert(counts_copy)

        print(f"📊 Updated counts: {counts_copy}")
        time.sleep(2)  # YOLO can run slower than video stream

# ----------------------------------
# AUDIO PANIC DETECTION (BLINDSPOT AI)
# ----------------------------------
AUDIO_ALERT_ACTIVE = False
AUDIO_VOLUME_THRESHOLD = 150
LAST_PANIC_TIME = 0  # <--- NEW: Tracks when the last loud noise happened

def listen_for_panic():
    global AUDIO_ALERT_ACTIVE, AUDIO_VOLUME_THRESHOLD, LAST_PANIC_TIME
    
    def audio_callback(indata, frames, time_info, status):
        global AUDIO_ALERT_ACTIVE, AUDIO_VOLUME_THRESHOLD, LAST_PANIC_TIME
        
        volume_norm = np.linalg.norm(indata) * 10 
        current_time = time.time()
        
        if volume_norm > AUDIO_VOLUME_THRESHOLD:
            LAST_PANIC_TIME = current_time  # Record the exact time of the noise
            if not AUDIO_ALERT_ACTIVE:
                print(f"\n🚨 [BLINDSPOT AI] AUDIO PANIC! Volume: {int(volume_norm)}")
                AUDIO_ALERT_ACTIVE = True
        else:
            # ONLY turn off the alert if 5 seconds have passed since the last loud noise
            if current_time - LAST_PANIC_TIME > 5.0:
                AUDIO_ALERT_ACTIVE = False

    try:
        with sd.InputStream(callback=audio_callback):
            print("🎙️ Audio Blindspot Monitor Started...")
            while True:
                time.sleep(1)
    except Exception as e:
        print(f"⚠️ Audio Monitor failed: {e}")

# ----------------------------------
# FLASK APIs
# ----------------------------------

# AUTHENTICATION
@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    """Authenticate user and return role"""
    if request.method == "OPTIONS":
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        role = data.get("role", "").strip()
        
        if not username or not password or not role:
            return jsonify({"error": "Username, password, and role are required"}), 400
        
        if role not in ["operator", "admin"]:
            return jsonify({"error": "Invalid role"}), 400
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Check credentials
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT role FROM users WHERE username = ? AND password_hash = ? AND role = ?',
            (username, password_hash, role)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({"success": True, "role": role})
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

# OPERATOR APIs
@app.route("/video_feed/<zone>")
def video_feed(zone):
    """FAST RAW MJPEG video stream - NO YOLO, direct camera feed"""
    zone = zone.capitalize()
    if zone not in VIDEO_SOURCES:
        return jsonify({"error": "Invalid zone"}), 404
    
    if zone not in streaming_caps:
        def error_generate():
            blank = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank, f"Camera not available: {zone}", (50, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            _, encoded = cv2.imencode('.jpg', blank)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   encoded.tobytes() + b'\r\n')
        return Response(error_generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    cap = streaming_caps[zone]

    def generate():
        src = VIDEO_SOURCES.get(zone, "0")

        while True:
            try:
                if isinstance(src, str) and src.startswith("http"):
                    snapshot_url = src.replace("/video", "/shot.jpg").replace("/videofeed", "/shot.jpg")
                    with urllib.request.urlopen(snapshot_url, timeout=2) as resp:
                        img_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)
                        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        if frame is not None:
                            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                            result, encoded_image = cv2.imencode('.jpg', frame, encode_param)
                            if result:
                                yield (b'--frame\r\n'
                                       b'Content-Type: image/jpeg\r\n\r\n' +
                                       encoded_image.tobytes() + b'\r\n')
                else:
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        time.sleep(0.033)
                        continue
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                    result, encoded_image = cv2.imencode('.jpg', frame, encode_param)
                    if result:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' +
                               encoded_image.tobytes() + b'\r\n')

            except Exception as e:
                print(f"❌ Stream error for {zone}: {e}")
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank, f"Reconnecting {zone}...", (50, 240),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                _, encoded = cv2.imencode('.jpg', blank)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       encoded.tobytes() + b'\r\n')

            time.sleep(0.05)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/live_counts")
def live_counts():
    """Get current crowd counts per zone (thread-safe read)"""
    with counts_lock:
        return jsonify(latest_counts.copy())

@app.route("/status")
def status():
    """Get current crowd status (NORMAL / WARNING / OVERCROWDED) - thread-safe"""
    global AUDIO_ALERT_ACTIVE
    with counts_lock:
        counts_copy = latest_counts.copy()
    
    total_crowd = sum(counts_copy.values())
    thresholds = load_thresholds()
    total_threshold = thresholds["total_crowd"]

    
    
    # Determine status based on total crowd
    if total_crowd >= total_threshold:
        status = "OVERCROWDED"
    elif total_crowd >= total_threshold * 0.7:  # 70% of threshold
        status = "WARNING"
    else:
        status = "NORMAL"
    
    return jsonify({
        "status": status,
        "total_crowd": total_crowd,
        "threshold": total_threshold,
        "zones": counts_copy,
        "audio_alert": AUDIO_ALERT_ACTIVE
    })

@app.route("/history")
def history():
    global mongo_connected
    if mongo_connected and collection is not None:
        try:
            records = list(collection.find().sort("timestamp", -1).limit(50))
            return jsonify([
                {"timestamp": r["timestamp"], "count": r["count"]}
                for r in records
            ])
        except Exception as e:
            print(f"❌ Error fetching history: {e}")
            return jsonify([])
    else:
        return jsonify([])  # Return empty list if MongoDB not connected

@app.route("/video_status")
def video_status():
    """Diagnostic endpoint to check video status"""
    with counts_lock:
        counts_copy = latest_counts.copy()
    
    status = {}
    for zone, path in VIDEO_SOURCES.items():
        status[zone] = {
            "source": path,
            "streaming_opened": zone in streaming_caps and streaming_caps[zone].isOpened() if zone in streaming_caps else False,
            "yolo_opened": zone in yolo_caps and yolo_caps[zone].isOpened() if zone in yolo_caps else False,
            "current_count": counts_copy.get(zone, 0)
        }
    return jsonify(status)

@app.route("/alert_config", methods=["GET"])
def get_alert_config():
    """Get current alert configuration"""
    thresholds = load_thresholds()
    return jsonify({
        "threshold_total_crowd": thresholds["total_crowd"],
        "threshold_zones": thresholds["zones"],
        "recipient_phones": RECIPIENT_PHONE_NUMBERS if RECIPIENT_PHONE_NUMBERS else [],
        "twilio_configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
        "sms_api_configured": bool(SMS_API_URL and SMS_API_KEY),
        "alert_cooldown_minutes": ALERT_COOLDOWN_MINUTES,
        "mongodb_connected": mongo_connected
    })

@app.route("/mongodb_status", methods=["GET"])
def mongodb_status():
    """Check MongoDB connection status"""
    global mongo_connected
    
    status = {
        "connected": mongo_connected,
        "message": ""
    }
    
    if mongo_connected:
        try:
            # Test the connection
            client.admin.command('ping')
            status["message"] = "✅ MongoDB is connected and responding"
            status["database"] = db.name if db else "unknown"
            status["collections"] = {
                "crowd_data": collection.name if collection else None,
                "thresholds": thresholds_collection.name if thresholds_collection else None
            }
        except Exception as e:
            status["connected"] = False
            status["message"] = f"❌ MongoDB connection test failed: {str(e)}"
            mongo_connected = False
    else:
        status["message"] = "⚠️ MongoDB is not connected"
        status["fallback"] = "Using local file storage (thresholds.json)"
    
    return jsonify(status)

@app.route("/thresholds", methods=["GET"])
@app.route("/threshold", methods=["GET"])
def get_thresholds():
    """Get current threshold values"""
    thresholds = load_thresholds()
    return jsonify(thresholds)

@app.route("/thresholds", methods=["POST"])
@app.route("/threshold", methods=["POST"])
def update_thresholds():
    """Update threshold values"""
    global THRESHOLD_TOTAL_CROWD, THRESHOLD_ZONE_SPECIFIC
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get values from request
        total_crowd = data.get("total_crowd")
        zones = data.get("zones", {})
        
        # Validate
        if total_crowd is not None:
            total_crowd = int(total_crowd)
            if total_crowd < 0:
                return jsonify({"error": "Total crowd threshold must be >= 0"}), 400
        
        # Validate zone thresholds
        validated_zones = {}
        current_thresholds = load_thresholds()  # Load current to preserve missing zones
        for zone in ["Entrance", "Queue", "Sanctum", "Exit"]:
            if zone in zones:
                value = int(zones[zone])
                if value < 0:
                    return jsonify({"error": f"{zone} threshold must be >= 0"}), 400
                validated_zones[zone] = value
            else:
                # Keep existing value if not provided
                validated_zones[zone] = current_thresholds["zones"].get(zone, 10)
        
        # Use existing total_crowd if not provided
        if total_crowd is None:
            total_crowd = current_thresholds["total_crowd"]
        
        # IMPORTANT: Update global variables FIRST (before saving)
        # This ensures alerts use new thresholds immediately
        THRESHOLD_TOTAL_CROWD = total_crowd
        THRESHOLD_ZONE_SPECIFIC = validated_zones
        
        print(f"🔄 Thresholds updated in memory: Total={total_crowd}, Zones={validated_zones}")
        
        # Then save to persistent storage (MongoDB or file)
        save_success = save_thresholds(total_crowd, validated_zones)
        
        if save_success:
            print(f"✅ Thresholds saved and active immediately")
        else:
            print(f"⚠️  Thresholds updated in memory but save to storage failed")
        
        # 🔍 IMMEDIATELY CHECK CURRENT COUNTS AGAINST NEW THRESHOLDS
        print(f"🔍 Checking current counts against new thresholds...")
        current_counts = latest_counts.copy()
        total_current = sum(current_counts.values())
        
        alerts_triggered = []
        
        # Check total crowd threshold
        if total_current >= total_crowd:
            alerts_triggered.append({
                "type": "Total Crowd",
                "count": total_current,
                "threshold": total_crowd,
                "message": f"🚨 ALERT: Current total crowd count ({total_current}) already exceeds new threshold ({total_crowd})!\n\nZone breakdown:\n" + 
                           "\n".join([f"{zone}: {count} heads" for zone, count in current_counts.items()])
            })
        
        # Check zone-specific thresholds
        for zone, count in current_counts.items():
            zone_threshold = validated_zones.get(zone, 10)
            if count >= zone_threshold:
                alerts_triggered.append({
                    "type": f"{zone} Zone",
                    "count": count,
                    "threshold": zone_threshold,
                    "message": f"🚨 ALERT: Current {zone} zone count ({count} heads) already exceeds new threshold ({zone_threshold})!\n\nTotal crowd: {total_current} heads"
                })
        
        # Send alerts if any thresholds are exceeded
        if alerts_triggered:
            print(f"📱 {len(alerts_triggered)} alert(s) triggered by new thresholds")
            for alert in alerts_triggered:
                print(f"   - {alert['type']}: Count {alert['count']} >= Threshold {alert['threshold']}")
                if RECIPIENT_PHONE_NUMBERS:
                    send_sms_notification(RECIPIENT_PHONE_NUMBERS, alert['message'])
                else:
                    print(f"   ⚠️  No recipient phone numbers configured - alert not sent")
        else:
            print(f"✅ Current counts are within new thresholds")
            print(f"   Total: {total_current} < {total_crowd}")
            for zone, count in current_counts.items():
                threshold = validated_zones.get(zone, 10)
                print(f"   {zone}: {count} < {threshold}")
        
        # Return response with alert information
        response_data = {
            "success": True,
            "message": "Thresholds updated successfully and are now active",
            "thresholds": {
                "total_crowd": total_crowd,
                "zones": validated_zones
            },
            "current_counts": current_counts,
            "total_current": total_current,
            "alerts_triggered": len(alerts_triggered),
            "alerts": [{"type": a["type"], "count": a["count"], "threshold": a["threshold"]} for a in alerts_triggered]
        }
        
        if not save_success:
            response_data["warning"] = "Thresholds not persisted - will reset on restart"
        
        return jsonify(response_data)
            
    except ValueError as e:
        return jsonify({"error": f"Invalid value: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/test_sms", methods=["POST"])
def test_sms():
    """Test SMS sending functionality"""
    data = request.get_json() or {}
    test_number = data.get("phone_number", RECIPIENT_PHONE_NUMBERS[0] if RECIPIENT_PHONE_NUMBERS else "")
    test_message = data.get("message", "🧪 Test message from Temple Crowd Management System")
    
    if not test_number:
        return jsonify({"error": "No phone number provided"}), 400
    
    success = send_sms_notification([test_number], test_message)
    
    if success:
        return jsonify({"status": "success", "message": f"SMS sent to {test_number}"})
    else:
        return jsonify({"status": "error", "message": "Failed to send SMS. Check credentials and configuration."}), 500

# ----------------------------------
# MAIN
# ----------------------------------
if __name__ == "__main__":
    print("✅ YOLO + Mongo Backend Started")
    print("📡 API running on http://localhost:5001")
    
    # Print MongoDB status
    if mongo_connected:
        print("💾 MongoDB: CONNECTED ✅")
        print(f"   Database: temple_crowd_db")
        print(f"   Collections: crowd_data, thresholds")
    else:
        print("💾 MongoDB: NOT CONNECTED ⚠️")
        print("   Thresholds will be saved to: thresholds.json")
        print("   Historical data will not be saved")
        print("   Check MongoDB connection: http://localhost:5001/mongodb_status")
    
    # Print SMS configuration status
    if TWILIO_ACCOUNT_SID or SMS_API_URL:
        print("📱 SMS notifications: CONFIGURED")
        if RECIPIENT_PHONE_NUMBERS:
            print(f"   Recipients: {', '.join(RECIPIENT_PHONE_NUMBERS)}")
        else:
            print("   ⚠️  No recipient phone numbers configured")
    else:
        print("📱 SMS notifications: NOT CONFIGURED")
        print("   See SMS_SETUP.md for configuration instructions")
    
    print(f"🚨 Alert thresholds - Total: {THRESHOLD_TOTAL_CROWD}, Zones: {THRESHOLD_ZONE_SPECIFIC}")

    threading.Thread(target=yolo_video_loop, daemon=True).start()
    #threading.Thread(target=yolo_video_loop, daemon=True).start()
    
    # --- START AUDIO LISTENER ---
    threading.Thread(target=listen_for_panic, daemon=True).start()


    app.run(host="0.0.0.0", port=5001, debug=False)
