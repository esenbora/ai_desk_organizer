# DeskOpt - AI Ergonomics Engine

## Overview
Desktop application that analyzes desk setups and provides ergonomic recommendations using computer vision and AI.

## Features
- 4-point calibration using reference object (credit card)
- AI-powered desk item detection
- Role-specific ergonomic recommendations
- Visual overlay with placement suggestions
- Profile management for different users

## Installation
```bash
pip install -r requirements.txt
python src/main.py
```

## Project Structure
```
src/
├── core/           # Database and business logic
├── gui/            # Desktop interface
├── ai/             # Computer vision and ML models
└── utils/          # Helper functions
data/               # Database and scans
tests/              # Unit tests
docs/               # Documentation
```