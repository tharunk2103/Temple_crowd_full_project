# Quick Start: SMS Alerts

## Quick Setup (5 minutes)

### 1. Install python-dotenv (optional but recommended)
```bash
pip install python-dotenv
```

### 2. Create .env file
```bash
cp .env.example .env
```

### 3. Edit .env file with your Twilio credentials

Get free Twilio account at: https://www.twilio.com

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
RECIPIENT_PHONE_NUMBERS=+1234567890
THRESHOLD_TOTAL_CROWD=20
```

### 4. Restart the server
The system will automatically send SMS alerts when thresholds are exceeded!

## Test SMS

```bash
curl -X POST http://localhost:5001/test_sms \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890", "message": "Test"}'
```

## Check Configuration

```bash
curl http://localhost:5001/alert_config
```

## How It Works

- Monitors crowd counts every 3 seconds
- Sends SMS when:
  - Total crowd ≥ threshold, OR
  - Any zone count ≥ its threshold
- Prevents spam: Max 1 alert per 5 minutes per threshold

See `SMS_SETUP.md` for detailed instructions.
