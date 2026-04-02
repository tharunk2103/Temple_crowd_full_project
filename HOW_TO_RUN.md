# How to Run the Server

## ✅ Step 1: Install python-dotenv (if not already installed)

```bash
cd /Users/tharunkumar/Desktop/temple_crowd_project
source venv/bin/activate
pip install python-dotenv
```

## ✅ Step 2: Verify .env file exists

The .env file should be in:
```
/Users/tharunkumar/Desktop/temple_crowd_project/.env
```

## ✅ Step 3: Run the Server

```bash
cd /Users/tharunkumar/Desktop/temple_crowd_project
source venv/bin/activate
python yolo_processor_mongo.py
```

## ✅ What You Should See

When the server starts, you should see:

```
✅ Loaded environment variables from .env file
✅ YOLO + Mongo Backend Started
📡 API running on http://localhost:5001
📱 SMS notifications: CONFIGURED
   Recipients: +1234567890
🚨 Alert thresholds - Total: 20, Zones: {'Entrance': 10, 'Queue': 15, 'Sanctum': 8, 'Exit': 10}
✅ Loaded video for Entrance: videos/entrance.mp4
✅ Loaded video for Queue: videos/queue.mp4
✅ Loaded video for Exit: videos/exit.mp4
```

## ⚠️ If You See "SMS notifications: NOT CONFIGURED"

This means:
- Either .env file is not being loaded (check python-dotenv is installed)
- Or credentials are not set in .env file

## 🔍 Test SMS Configuration

After server starts, test it:
```bash
curl http://localhost:5001/alert_config
```

This will show your current configuration.

## 📱 Test SMS Sending

```bash
curl -X POST http://localhost:5001/test_sms \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "Test message"}'
```

## 🚀 The Server is Ready!

Once you see the startup messages, the server is:
- ✅ Processing videos
- ✅ Detecting heads
- ✅ Monitoring thresholds
- ✅ Ready to send SMS alerts when thresholds are exceeded
