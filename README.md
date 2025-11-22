# DeskOpt - AI Ergonomics Engine

**Version 1.0.0**

An AI-powered desktop ergonomics analyzer that helps optimize your workspace setup using computer vision and ergonomic best practices.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green.svg)
![YOLOv8](https://img.shields.io/badge/YOLOv8-8.0+-orange.svg)

## 🎯 Features

- **AI-Powered Detection**: Uses YOLOv8 for accurate desk item detection
- **Role-Specific Analysis**: Tailored ergonomic rules for Coders, Artists, Gamers, and Admins
- **Precision Calibration**: 4-point credit card calibration for accurate measurements
- **Real-time Feedback**: Visual overlay showing detected items and recommendations
- **Ergonomic Scoring**: 0-100 score based on workspace optimization
- **Progress Tracking**: Non-blocking UI with real-time progress updates
- **Professional Logging**: Rotating logs with detailed debugging information

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.10 or higher
python --version

# Install dependencies
pip install -r requirements.txt
```

### Run the Application

```bash
python run_deskopt.py
```

### First Time Setup

1. **Import a desk photo** (PNG, JPG, JPEG, or BMP)
2. **Calibrate** by clicking the 4 corners of a credit card in your photo
3. **Mark desk edges** by clicking the 4 corners of your desk surface
4. **Create a profile** with your name, role, and handedness
5. **Click "Analyze Setup"** to get ergonomic recommendations

## 📋 Requirements

- `PyQt6 >= 6.5.0` - Desktop GUI framework
- `opencv-python >= 4.8.0` - Image processing
- `ultralytics >= 8.0.0` - YOLOv8 object detection
- `torch >= 2.0.0` - Deep learning backend
- `numpy >= 1.24.0` - Numerical operations

See `requirements.txt` for complete list.

## 🏗️ Project Structure

```
ai_desk_organizer/
├── src/
│   ├── ai/                  # AI detection modules
│   ├── core/                # Business logic
│   ├── gui/                 # User interface
│   ├── utils/               # Utility modules
│   └── config.py            # Configuration
├── data/                    # Application data
├── logs/                    # Log files
├── tests/                   # Unit tests
└── run_deskopt.py          # Main launcher
```

## 🧪 Testing

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

**Test Coverage**: ~85%

## ⚙️ Configuration

All settings are in `src/config.py`:

```python
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
MAX_IMAGE_SIZE_MB = 50
CARD_WIDTH_CM = 8.5  # Standard credit card
```

## 🎮 Supported Roles

- **Coder**: Keyboard/mouse centered, monitor at arm's length
- **Artist**: Drawing tablet centered, good lighting
- **Gamer**: Close monitor, wide mouse space
- **Admin**: Balanced setup, phone accessible

## 🔍 Detected Items

Keyboard, Mouse, Monitor, Laptop, Phone, Tablet, Coffee Mug, Notebook, Pen, Desk Lamp, Speaker, Headphones

## 📈 Ergonomic Scoring

- **80-100**: Excellent (Green)
- **60-79**: Good (Orange)
- **0-59**: Needs Improvement (Red)

## 🐛 Troubleshooting

**Image won't load**:
- Check file format and size (<50MB)
- Ensure file is accessible

**No items detected**:
- Use better lighting
- Try a different camera angle

**Application crashes**:
- Check logs in `logs/deskopt.log`
- Verify Python version >= 3.10

## 📝 Logging

Logs in `logs/deskopt.log` with rotation:
- Max size: 10MB
- Backups: 5 files

## 📜 License

MIT License

---

**Made for better ergonomics**
