# Threshold Configuration Guide

## ✅ Manual Threshold Configuration

You can now configure thresholds manually through the web interface or API - no code changes needed!

## 🖥️ Method 1: Web Interface (Easiest)

### Step 1: Open Streamlit Dashboard
```bash
streamlit run app.py
```

### Step 2: Navigate to Threshold Settings
1. Open the sidebar (click the arrow on the left)
2. Select "⚙️ Threshold Settings"
3. Or use URL: `http://localhost:8501/?view=thresholds`

### Step 3: Configure Thresholds
- **Total Crowd Threshold**: Maximum total people across all zones
- **Zone Thresholds**: Individual limits for each zone
  - Entrance Zone
  - Queue Zone
  - Sanctum Zone
  - Exit Zone

### Step 4: Save
Click the "💾 Save Thresholds" button. Changes take effect immediately!

## 🔌 Method 2: API Endpoints

### Get Current Thresholds
```bash
curl http://localhost:5001/thresholds
```

Response:
```json
{
  "total_crowd": 20,
  "zones": {
    "Entrance": 10,
    "Queue": 15,
    "Sanctum": 8,
    "Exit": 10
  }
}
```

### Update Thresholds
```bash
curl -X POST http://localhost:5001/thresholds \
  -H "Content-Type: application/json" \
  -d '{
    "total_crowd": 25,
    "zones": {
      "Entrance": 12,
      "Queue": 18,
      "Sanctum": 10,
      "Exit": 12
    }
  }'
```

### Update Only Total Crowd
```bash
curl -X POST http://localhost:5001/thresholds \
  -H "Content-Type: application/json" \
  -d '{"total_crowd": 30}'
```

### Update Only Zone Thresholds
```bash
curl -X POST http://localhost:5001/thresholds \
  -H "Content-Type: application/json" \
  -d '{
    "zones": {
      "Queue": 20
    }
  }'
```

## 💾 Storage

Thresholds are stored in **MongoDB** in the `thresholds` collection. This means:
- ✅ Settings persist across server restarts
- ✅ No need to edit code or .env file
- ✅ Changes take effect immediately
- ✅ Multiple users can update via web interface

## 🔄 How It Works

1. **Initial Load**: On server start, thresholds are loaded from MongoDB
2. **Fallback**: If MongoDB doesn't have thresholds, it uses:
   - Environment variables (from .env file)
   - Default values (hardcoded)
3. **Dynamic Updates**: Thresholds are reloaded every time alerts are checked
4. **Immediate Effect**: Changes take effect without restarting the server

## 📊 Example Use Cases

### Scenario 1: Festival Day
Increase thresholds for high-traffic days:
- Total Crowd: 50
- Queue: 30
- Other zones: 15

### Scenario 2: Regular Day
Normal thresholds:
- Total Crowd: 20
- Queue: 15
- Other zones: 10

### Scenario 3: Maintenance Day
Lower thresholds for safety:
- Total Crowd: 10
- All zones: 5

## ⚠️ Important Notes

1. **Validation**: All thresholds must be >= 0
2. **No Restart Needed**: Changes apply immediately
3. **Persistent**: Settings saved in MongoDB
4. **Backup**: Consider exporting thresholds periodically

## 🔍 Verify Configuration

Check current thresholds:
```bash
curl http://localhost:5001/alert_config
```

This shows all alert configuration including thresholds.

## 🚨 Alert Behavior

- Alerts are sent when thresholds are exceeded
- Each threshold has a 5-minute cooldown (prevents spam)
- Zone-specific alerts are separate from total crowd alerts
- Both can trigger simultaneously

## 📝 Default Values

If no thresholds are configured:
- Total Crowd: 20
- Entrance: 10
- Queue: 15
- Sanctum: 8
- Exit: 10

These can be changed anytime through the web interface or API!
