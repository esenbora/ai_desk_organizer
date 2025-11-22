"""
Pytest configuration and fixtures
"""
import pytest
import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_db_path(temp_dir):
    """Provide a temporary database path"""
    return os.path.join(temp_dir, "test_deskopt.db")


@pytest.fixture
def sample_image_path():
    """Provide path to sample test image"""
    # Create a simple test image if needed
    test_img_path = Path(__file__).parent / "fixtures" / "test_desk.jpg"
    return str(test_img_path) if test_img_path.exists() else None


@pytest.fixture
def sample_calibration_points():
    """Provide sample calibration points for a credit card"""
    # Points forming an 85x54 pixel rectangle (simulating 8.5x5.4 cm card at 10 px/cm)
    return [
        (0, 0),      # Top-left
        (85, 0),     # Top-right
        (85, 54),    # Bottom-right
        (0, 54)      # Bottom-left
    ]


@pytest.fixture
def sample_desk_corners():
    """Provide sample desk corner points"""
    # Points forming a 1200x600 pixel rectangle
    return [
        (100, 100),    # Top-left
        (1300, 100),   # Top-right
        (1300, 700),   # Bottom-right
        (100, 700)     # Bottom-left
    ]


@pytest.fixture
def sample_detected_items():
    """Provide sample detected items"""
    return [
        {
            'slug': 'keyboard',
            'x': 200,
            'y': 300,
            'width': 300,
            'height': 100,
            'confidence': 0.85,
            'rotation': 0
        },
        {
            'slug': 'mouse',
            'x': 550,
            'y': 320,
            'width': 60,
            'height': 90,
            'confidence': 0.78,
            'rotation': 0
        },
        {
            'slug': 'monitor',
            'x': 400,
            'y': 150,
            'width': 400,
            'height': 250,
            'confidence': 0.92,
            'rotation': 0
        }
    ]
