# Why Thresholds Are Not Saving to MongoDB

## 🔍 How to Check MongoDB Status

### Method 1: Check Server Startup Logs
When you start the server, look for:
- `✅ MongoDB connected successfully` = MongoDB is working
- `⚠️ MongoDB connection failed` = MongoDB is NOT connected

### Method 2: Use API Endpoint
```bash
curl http://localhost:5001/mongodb_status
```

This will show:
```json
{
  "connected": true/false,
  "message": "Status message",
  "database": "temple_crowd_db",
  "collections": {...}
}
```

### Method 3: Check Alert Config
```bash
curl http://localhost:5001/alert_config
```

Look for `"mongodb_connected": true/false`

## ❌ Common Reasons MongoDB Isn't Saving

### 1. **MongoDB Connection Failed at Startup**
- **Symptom**: See `⚠️ MongoDB connection failed` in logs
- **Cause**: SSL handshake error, network issue, wrong credentials
- **Solution**: Check MongoDB Atlas IP whitelist, update pymongo

### 2. **Connection Lost During Runtime**
- **Symptom**: Started connected but later fails
- **Cause**: Network interruption, MongoDB Atlas maintenance
- **Solution**: The code now auto-reconnects when saving

### 3. **SSL/TLS Certificate Issues**
- **Symptom**: SSL handshake errors
- **Cause**: Outdated certificates, network restrictions
- **Solution**: Update pymongo: `pip install --upgrade pymongo`

### 4. **IP Address Not Whitelisted**
- **Symptom**: Connection timeout
- **Cause**: Your IP is not in MongoDB Atlas whitelist
- **Solution**: 
  1. Go to https://cloud.mongodb.com
  2. Network Access → Add IP Address
  3. Add your current IP or `0.0.0.0/0` (for testing only)

## ✅ What Happens Now

### If MongoDB is Connected:
```
✅ Thresholds saved to MongoDB (matched: 1, modified: 1)
```

### If MongoDB is NOT Connected:
```
⚠️  Error saving to MongoDB: [error details]
✅ Thresholds saved to local file: thresholds.json
```

**Thresholds are ALWAYS saved** - either to MongoDB OR to local file!

## 🔧 How to Fix MongoDB Connection

### Step 1: Check MongoDB Atlas
1. Go to https://cloud.mongodb.com
2. Verify your cluster is running
3. Check Network Access (IP whitelist)
4. Verify database user credentials

### Step 2: Test Connection
```bash
# Test MongoDB connection
curl http://localhost:5001/mongodb_status
```

### Step 3: Update pymongo
```bash
pip install --upgrade pymongo
```

### Step 4: Restart Server
After fixing issues, restart the server:
```bash
python yolo_processor_mongo.py
```

## 📊 Current Behavior

The system now:
1. **Tries MongoDB first** - If connected, saves there
2. **Auto-reconnects** - Attempts to reconnect if connection lost
3. **Falls back to file** - Saves to `thresholds.json` if MongoDB fails
4. **Always persists** - Thresholds are never lost!

## 🔍 Debugging Steps

1. **Check startup logs** for MongoDB connection status
2. **Check MongoDB status endpoint**: `curl http://localhost:5001/mongodb_status`
3. **Try saving thresholds** and watch console output
4. **Check if thresholds.json exists** (means MongoDB failed, file used)
5. **Verify MongoDB Atlas** is accessible from your network

## 💡 Important Notes

- **Thresholds are ALWAYS saved** - either MongoDB or local file
- **Local file is backup** - `thresholds.json` in project folder
- **Auto-reconnection** - System tries to reconnect when saving
- **No data loss** - Even if MongoDB fails, thresholds persist

## 🎯 Quick Fix

If MongoDB keeps failing, the system automatically uses local file storage. Your thresholds will still:
- ✅ Be saved
- ✅ Persist across restarts
- ✅ Work perfectly

MongoDB is optional - the system works fine without it!
