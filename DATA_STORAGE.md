# Where Crowd Data is Stored

## 📍 Primary Storage: MongoDB Atlas

### Database Details
- **Database Name**: `temple_crowd_db`
- **Collection Name**: `crowd_data`
- **Connection**: MongoDB Atlas Cloud
- **URI**: `mongodb+srv://temple_crowd:kanchi@123@templecrowd.pywbjlx.mongodb.net/temple_crowd_db`

### What Data is Stored

Every 3 seconds, the system stores:
```json
{
  "timestamp": "2026-01-22T22:10:24.192525",
  "zones": {
    "Entrance": 5,
    "Queue": 12,
    "Sanctum": 4,
    "Exit": 3
  },
  "count": 24
}
```

### Data Structure
- **timestamp**: When the count was recorded
- **zones**: Head count for each zone (Entrance, Queue, Sanctum, Exit)
- **count**: Total head count across all zones

### Access MongoDB Data

**Via MongoDB Atlas Dashboard:**
1. Go to https://cloud.mongodb.com
2. Select your cluster
3. Click "Browse Collections"
4. Select `temple_crowd_db` → `crowd_data`

**Via API:**
```bash
# Get historical data (last 50 records)
curl http://localhost:5001/history
```

**Via Python:**
```python
from pymongo import MongoClient
client = MongoClient("** Enter your mongodb url**")
db = client["temple_crowd_db"]
collection = db["crowd_data"]

# Get all records
for record in collection.find():
    print(record)
```

## 📁 Secondary Storage: Local Files

### Thresholds Storage
- **File**: `thresholds.json`
- **Location**: `/Users/tharunkumar/Desktop/temple_crowd_project/thresholds.json`
- **Content**: Threshold configurations

### Frame Images
- **Latest frames**: `latest_frame_entrance.jpg`, `latest_frame_queue.jpg`, etc.
- **Heatmap**: `latest_heatmap.jpg`
- **Location**: Project root directory

## ⚠️ Important Notes

### If MongoDB is NOT Connected:
- ❌ **Crowd data is NOT saved** (only in memory)
- ✅ **Thresholds are saved** to `thresholds.json` file
- ✅ **App continues working** (video processing, alerts, etc.)
- ⚠️ **No historical data** is stored

### If MongoDB IS Connected:
- ✅ **Crowd data is saved** every 3 seconds
- ✅ **Thresholds are saved** to MongoDB
- ✅ **Historical data** is available via `/history` API
- ✅ **All data persists** across server restarts

## 🔍 Check Data Storage Status

### Check MongoDB Connection:
```bash
curl http://localhost:5001/mongodb_status
```

### Check if Data is Being Saved:
Look at server console logs:
- `✅ MongoDB connected successfully` = Data is being saved
- `⚠️ MongoDB connection failed` = Data is NOT being saved

### View Historical Data:
```bash
curl http://localhost:5001/history | python -m json.tool
```

## 📊 Data Storage Locations Summary

| Data Type | Primary Location | Backup Location | Status |
|-----------|-----------------|-----------------|--------|
| **Crowd Counts** | MongoDB Atlas (`crowd_data` collection) | None (lost if MongoDB fails) | ⚠️ Requires MongoDB |
| **Thresholds** | MongoDB Atlas (`thresholds` collection) | `thresholds.json` file | ✅ Always saved |
| **Video Frames** | Local files (`latest_frame_*.jpg`) | N/A | ✅ Always saved |
| **Heatmaps** | Local files (`latest_heatmap.jpg`) | N/A | ✅ Always saved |

## 💡 Recommendations

1. **Ensure MongoDB is connected** for historical data storage
2. **Check MongoDB Atlas** regularly to verify data is being saved
3. **Backup thresholds.json** periodically
4. **Monitor storage** - MongoDB Atlas has free tier limits (512MB)

## 🔧 Troubleshooting

### Data Not Being Saved?

1. **Check MongoDB connection:**
   ```bash
   curl http://localhost:5001/mongodb_status
   ```

2. **Check server logs** for MongoDB connection status

3. **Verify MongoDB Atlas:**
   - Cluster is running
   - IP address is whitelisted
   - Credentials are correct

4. **Check if data exists:**
   ```bash
   curl http://localhost:5001/history
   ```
   If empty array `[]`, no data is being saved.

## 📈 Data Retention

- **MongoDB**: Stores all data (no automatic deletion)
- **API History**: Returns last 50 records
- **Local Files**: Overwritten each cycle (no history)

To query more historical data, use MongoDB directly or modify the `/history` endpoint limit.
