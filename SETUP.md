# Parkify Backend - Setup Guide

## Required Configuration

Before running the backend locally, you need to set up the following keys and credentials.

---

### 1. Environment Variables (`.env` file)

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Edit `.env` with the following:

| Variable | Description | How to Get |
|---|---|---|
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens. Use a long random string. | Generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `FIREBASE_PROJECT_ID` | Your Firebase project ID | Firebase Console > Project Settings > General |
| `FIREBASE_PRIVATE_KEY` | Firebase Admin SDK private key (full RSA key) | Firebase Console > Project Settings > Service Accounts > Generate New Private Key (copy the `private_key` field from the JSON) |
| `FIREBASE_CLIENT_EMAIL` | Firebase service account email | Same JSON file, `client_email` field |

Example `.env`:
```env
DEBUG=true
JWT_SECRET_KEY=your-random-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
```

---

### 2. Firebase Service Account Key (for seeding data)

To run `seed_firebase.py` (seeds demo data into Firestore), you need the Firebase Admin SDK JSON file:

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** > **Service Accounts**
4. Click **Generate New Private Key**
5. Save the downloaded JSON file as `serviceAccountKey.json` in the project root

> This file is gitignored and will NOT be uploaded to GitHub.

---

### 3. ESP32 / IoT Device Keys (Optional)

If you're using ESP32 hardware for gate control, slot sensors, or ALPR, the device authentication keys are defined in `app/main.py`. The default demo keys are:

| Parking ID | Device Key |
|---|---|
| `parking_1` | `esp32_parking1_key` |
| `parking_2` | `esp32_parking2_key` |
| `parking_3` | `esp32_parking3_key` |
| `parking_4` | `esp32_parking4_key` |
| `parking_5` | `esp32_parking5_key` |

For production, change these to strong random keys and store them in environment variables.

---

## Quick Start

### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

### Windows
```cmd
setup.bat
```

### Manual Setup
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate.bat     # Windows

pip install -r requirements.txt

# Seed Firebase (optional - requires serviceAccountKey.json)
python seed_firebase.py

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints

| URL | Description |
|---|---|
| `http://localhost:8000` | Root - API info |
| `http://localhost:8000/docs` | Swagger UI (interactive API docs) |
| `http://localhost:8000/health` | Health check endpoint |
| `http://localhost:8000/dashboard` | Admin dashboard (Web UI) |

---

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@parkify.com | admin123 |
| User | amira@gmail.com | user123 |
| User | ahmed@gmail.com | user123 |
| User | sara@gmail.com | user123 |
| User | omar@gmail.com | user123 |
