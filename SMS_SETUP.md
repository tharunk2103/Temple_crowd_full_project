# SMS Alert Setup Guide

This guide will help you set up SMS notifications for the Temple Crowd Management System.

## Option 1: Using Twilio (Recommended)

### Step 1: Create a Twilio Account
1. Go to https://www.twilio.com
2. Sign up for a free account (includes $15.50 credit for testing)
3. Verify your phone number

### Step 2: Get Your Credentials
1. Go to https://www.twilio.com/console
2. Find your **Account SID** and **Auth Token**
3. Get a phone number from Twilio (free trial numbers available)

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890  # Your Twilio number
RECIPIENT_PHONE_NUMBERS=+1234567890,+0987654321  # Recipients (comma-separated)
```

### Step 4: Install python-dotenv (if using .env file)

```bash
pip install python-dotenv
```

Then update `yolo_processor_mongo.py` to load .env:
```python
from dotenv import load_dotenv
load_dotenv()
```

## Option 2: Using Generic SMS API

If you have access to another SMS API service:

```bash
SMS_API_URL=https://api.example.com/send-sms
SMS_API_KEY=your_api_key_here
RECIPIENT_PHONE_NUMBERS=+1234567890
```

## Configuration

### Threshold Settings

Set thresholds in environment variables or directly in code:

- `THRESHOLD_TOTAL_CROWD`: Total crowd count threshold (default: 20)
- `THRESHOLD_ENTRANCE`: Entrance zone threshold (default: 10)
- `THRESHOLD_QUEUE`: Queue zone threshold (default: 15)
- `THRESHOLD_SANCTUM`: Sanctum zone threshold (default: 8)
- `THRESHOLD_EXIT`: Exit zone threshold (default: 10)

### Alert Cooldown

Alerts are sent maximum once per 5 minutes per threshold to prevent spam. This can be adjusted in the code.

## Testing

### Test SMS via API

```bash
curl -X POST http://localhost:5001/test_sms \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "Test message"}'
```

### Check Configuration

```bash
curl http://localhost:5001/alert_config
```

## How It Works

1. The system continuously monitors crowd counts
2. When a threshold is exceeded:
   - Total crowd count exceeds `THRESHOLD_TOTAL_CROWD`, OR
   - Any zone count exceeds its specific threshold
3. SMS alerts are sent to all configured recipient numbers
4. Alerts include:
   - Which threshold was exceeded
   - Current count
   - Zone breakdown (for total crowd alerts)

## Example Alert Messages

**Total Crowd Alert:**
```
🚨 ALERT: Total crowd count (25) exceeded threshold (20)!

Zone breakdown:
Entrance: 5 heads
Queue: 12 heads
Sanctum: 4 heads
Exit: 4 heads
```

**Zone-Specific Alert:**
```
🚨 ALERT: Queue zone crowd count (18 heads) exceeded threshold (15)!

Total crowd: 25 heads
```

## Troubleshooting

1. **No SMS received:**
   - Check Twilio console for delivery status
   - Verify phone numbers are in correct format (+countrycode+number)
   - Check account balance/credits

2. **"Credentials not configured" error:**
   - Ensure environment variables are set correctly
   - Restart the server after setting environment variables

3. **Too many alerts:**
   - Increase `ALERT_COOLDOWN_MINUTES` in code
   - Adjust thresholds to be higher

## Security Notes

- Never commit `.env` file to git
- Keep Twilio credentials secure
- Use environment variables, not hardcoded credentials
