"""
Unit tests for CalibrationManager
"""
import pytest
import numpy as np
from core.calibration import CalibrationManager
from config import Config


class TestCalibrationManager:
    """Test CalibrationManager class"""

    @pytest.fixture
    def calibration(self):
        """Create a CalibrationManager instance"""
        return CalibrationManager()

    def test_init(self, calibration):
        """Test initialization"""
        assert calibration.card_width_cm == Config.CARD_WIDTH_CM
        assert calibration.card_height_cm == Config.CARD_HEIGHT_CM
        assert calibration.calibration_points == []
        assert calibration.scale_factor is None
        assert calibration.desk_corners == []

    def test_add_calibration_point(self, calibration):
        """Test adding calibration points"""
        count = calibration.add_calibration_point(10, 20)
        assert count == 1
        assert len(calibration.calibration_points) == 1
        assert calibration.calibration_points[0] == (10, 20)

        count = calibration.add_calibration_point(30, 40)
        assert count == 2
        assert len(calibration.calibration_points) == 2

    def test_add_desk_corner(self, calibration):
        """Test adding desk corners"""
        count = calibration.add_desk_corner(100, 100)
        assert count == 1
        assert len(calibration.desk_corners) == 1
        assert calibration.desk_corners[0] == (100, 100)

    def test_is_calibration_complete(self, calibration):
        """Test calibration completion check"""
        assert calibration.is_calibration_complete() is False

        calibration.add_calibration_point(0, 0)
        calibration.add_calibration_point(85, 0)
        calibration.add_calibration_point(85, 54)
        assert calibration.is_calibration_complete() is False

        calibration.add_calibration_point(0, 54)
        assert calibration.is_calibration_complete() is True

    def test_is_desk_complete(self, calibration):
        """Test desk corner completion check"""
        assert calibration.is_desk_complete() is False

        for i in range(3):
            calibration.add_desk_corner(i * 100, i * 100)
        assert calibration.is_desk_complete() is False

        calibration.add_desk_corner(300, 300)
        assert calibration.is_desk_complete() is True

    def test_calculate_scale_factor_perfect_square(self, calibration):
        """Test scale factor calculation with perfect square"""
        # 85x54 pixels for 8.5x5.4 cm card = 10 px/cm scale
        calibration.add_calibration_point(0, 0)
        calibration.add_calibration_point(85, 0)
        calibration.add_calibration_point(85, 54)
        calibration.add_calibration_point(0, 54)

        scale = calibration.calculate_scale_factor()
        assert scale is not None
        assert abs(scale - 10.0) < 0.1  # Should be ~10 px/cm

    def test_calculate_scale_factor_incomplete(self, calibration):
        """Test scale factor calculation with incomplete points"""
        calibration.add_calibration_point(0, 0)
        calibration.add_calibration_point(85, 0)

        scale = calibration.calculate_scale_factor()
        assert scale is None

    def test_calculate_scale_factor_too_close(self, calibration):
        """Test scale factor calculation with points too close"""
        # Points only 5 pixels apart (below MIN_CALIBRATION_PIXELS)
        calibration.add_calibration_point(0, 0)
        calibration.add_calibration_point(5, 0)
        calibration.add_calibration_point(5, 3)
        calibration.add_calibration_point(0, 3)

        with pytest.raises(ValueError, match="too close"):
            calibration.calculate_scale_factor()

    def test_calculate_scale_factor_unrealistic(self, calibration):
        """Test scale factor calculation with unrealistic points"""
        # Points way too far apart (above MAX_CALIBRATION_PIXELS)
        calibration.add_calibration_point(0, 0)
        calibration.add_calibration_point(15000, 0)
        calibration.add_calibration_point(15000, 10000)
        calibration.add_calibration_point(0, 10000)

        with pytest.raises(ValueError, match="unrealistic"):
            calibration.calculate_scale_factor()

    def test_calculate_scale_factor_perspective_warning(self, calibration, caplog):
        """Test perspective distortion warning"""
        # Create distorted rectangle (50% difference between X and Y scales)
        calibration.add_calibration_point(0, 0)
        calibration.add_calibration_point(85, 0)
        calibration.add_calibration_point(85, 100)  # Distorted height
        calibration.add_calibration_point(0, 100)

        scale = calibration.calculate_scale_factor()
        assert scale is not None
        assert "perspective distortion" in caplog.text.lower()

    def test_pixels_to_cm(self, calibration):
        """Test pixel to cm conversion"""
        calibration.scale_factor = 10.0  # 10 px/cm

        assert calibration.pixels_to_cm(100) == 10.0
        assert calibration.pixels_to_cm(50) == 5.0
        assert calibration.pixels_to_cm(0) == 0.0

    def test_pixels_to_cm_no_scale(self, calibration):
        """Test pixel to cm conversion without calibration"""
        assert calibration.pixels_to_cm(100) is None

    def test_cm_to_pixels(self, calibration):
        """Test cm to pixel conversion"""
        calibration.scale_factor = 10.0  # 10 px/cm

        assert calibration.cm_to_pixels(10.0) == 100.0
        assert calibration.cm_to_pixels(5.0) == 50.0
        assert calibration.cm_to_pixels(0) == 0.0

    def test_cm_to_pixels_no_scale(self, calibration):
        """Test cm to pixel conversion without calibration"""
        assert calibration.cm_to_pixels(10.0) is None

    def test_transform_to_desk_coordinates(self, calibration):
        """Test coordinate transformation to desk system"""
        # Set up calibration
        calibration.scale_factor = 10.0  # 10 px/cm

        # Set up desk corners (400x400 pixel desk, centered at 500, 500)
        calibration.add_desk_corner(300, 300)  # Top-left
        calibration.add_desk_corner(700, 300)  # Top-right
        calibration.add_desk_corner(700, 700)  # Bottom-right
        calibration.add_desk_corner(300, 700)  # Bottom-left

        # Desk center is at (500, 500)
        # Point at desk center should be (0, 0) in desk coordinates
        x_cm, y_cm = calibration.transform_to_desk_coordinates(500, 500)
        assert abs(x_cm) < 0.1
        assert abs(y_cm) < 0.1

        # Point 100 pixels right of center = 10 cm right
        x_cm, y_cm = calibration.transform_to_desk_coordinates(600, 500)
        assert abs(x_cm - 10.0) < 0.1
        assert abs(y_cm) < 0.1

    def test_transform_to_desk_coordinates_incomplete(self, calibration):
        """Test coordinate transformation with incomplete data"""
        x_cm, y_cm = calibration.transform_to_desk_coordinates(500, 500)
        assert x_cm is None
        assert y_cm is None

    def test_get_desk_dimensions_cm(self, calibration):
        """Test getting desk dimensions"""
        calibration.scale_factor = 10.0  # 10 px/cm

        # 1000x600 pixel desk
        calibration.add_desk_corner(0, 0)
        calibration.add_desk_corner(1000, 0)
        calibration.add_desk_corner(1000, 600)
        calibration.add_desk_corner(0, 600)

        width_cm, height_cm = calibration.get_desk_dimensions_cm()
        assert abs(width_cm - 100.0) < 0.1  # 1000 px / 10 px/cm = 100 cm
        assert abs(height_cm - 60.0) < 0.1   # 600 px / 10 px/cm = 60 cm

    def test_get_desk_dimensions_cm_incomplete(self, calibration):
        """Test getting desk dimensions with incomplete data"""
        width_cm, height_cm = calibration.get_desk_dimensions_cm()
        assert width_cm is None
        assert height_cm is None

    def test_get_desk_bounds_json(self, calibration):
        """Test JSON serialization of desk bounds"""
        calibration.add_desk_corner(0, 0)
        calibration.add_desk_corner(100, 0)
        calibration.add_desk_corner(100, 100)
        calibration.add_desk_corner(0, 100)

        json_str = calibration.get_desk_bounds_json()
        assert isinstance(json_str, str)
        assert "0" in json_str
        assert "100" in json_str

    def test_reset_calibration(self, calibration):
        """Test resetting calibration"""
        # Add some data
        calibration.add_calibration_point(0, 0)
        calibration.add_desk_corner(100, 100)
        calibration.scale_factor = 10.0

        # Reset
        calibration.reset_calibration()

        assert calibration.calibration_points == []
        assert calibration.desk_corners == []
        assert calibration.scale_factor is None
