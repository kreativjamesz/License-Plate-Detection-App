# 🚗 License Plate Detector App

Isang Python application na nag-detect ng license plates using camera at mga haarcascade models. Na-convert natin from face detection app to license plate detection app.

## ✨ Features

### 📹 Real-time Detection
- Live camera feed with license plate detection
- Visual detection boxes around detected plates
- Auto-save detections every 3 seconds (hindi ma-spam ang database)

### 📊 Dashboard
- Overview ng total detections
- Today's detection count
- Recent detection history
- Real-time statistics

### 📋 License Plates Management
- View all detected license plates sa table
- Search functionality
- Edit plate numbers
- Delete detections
- Pagination support

### 🛠️ Technical Features
- Multiple haarcascade models for better detection
- Non-maximum suppression para remove duplicate detections
- JSON-based storage (lightweight, no database required)
- Dark theme UI with CustomTkinter

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
python main.py
```

### 3. Login
- Use the existing login system
- Navigate to Dashboard o License Plates page

## 📁 Project Structure

```
app/
├── services/
│   ├── license_plate_service.py     # Main service for managing detections
│   └── plate/
│       └── detector.py              # License plate detection logic
├── ui/
│   └── pages/
│       ├── dashboard.py             # Dashboard with stats
│       └── license_plates.py       # Main detection page
└── models/                          # Haarcascade detection models
    ├── haarcascade_russian_plate_number.xml
    └── haarcascade_license_plate_rus_16stages.xml
```

## 🔍 Detection Models

Currently using Russian license plate models:
- `haarcascade_russian_plate_number.xml`
- `haarcascade_license_plate_rus_16stages.xml`

Pwede kang mag-add ng more models sa `app/models/` directory at automatically ma-load sila.

## 💾 Data Storage

- License plate detections stored sa `app/data/license_plates.json`
- 3-second interval between saves to prevent spam
- JSON format for easy backup/restore

## 🎛️ Usage

### Start Detection
1. Go to "License Plates" page
2. Click "Start Camera"
3. Point camera sa license plates
4. Automatic detection at saving every 3 seconds

### Manage Detections
- Search plates by number, location, or status
- Edit plate numbers if needed
- Delete false detections
- View pagination for large datasets

## 🛠️ Configuration

### Detection Parameters
Edit `app/services/plate/detector.py`:
- `scaleFactor`: Detection sensitivity
- `minNeighbors`: Minimum confirmations needed
- `minSize/maxSize`: Expected plate dimensions

### Save Interval
Edit `app/services/license_plate_service.py`:
- `save_interval`: Change from 3.0 seconds to desired interval

## 🔧 Adding More Models

1. Download haarcascade XML files
2. Place sa `app/models/` directory
3. Update `plate_models` dictionary sa `detector.py`
4. Models will be automatically loaded

## 📝 Notes

- Optimized for license plate detection
- Better performance than original face detection
- Clean, focused UI for plate management
- Easy to extend with more detection models

## 🎯 Next Steps

Pwede mo pa i-improve ng:
- OCR for reading plate text
- Database integration (PostgreSQL/MySQL)
- Better detection models
- Export functionality
- Real-time alerts
- License plate recognition accuracy tracking

---

**Na-convert na from face attendance system to license plate detector! Ready na for production use.** 🚀
