"""
Unit tests for Config module
"""
import pytest
from pathlib import Path
from config import Config


class TestConfig:
    """Test Config class"""

    def test_app_info(self):
        """Test application information constants"""
        assert Config.APP_NAME == "DeskOpt - AI Ergonomics Engine"
        assert Config.VERSION == "1.0.0"

    def test_paths_are_absolute(self):
        """Test that all paths are absolute"""
        assert Config.BASE_DIR.is_absolute()
        assert Config.DATA_DIR.is_absolute()
        assert Config.LOGS_DIR.is_absolute()
        assert Config.DB_PATH.is_absolute()

    def test_paths_are_pathlib(self):
        """Test that paths are Path objects"""
        assert isinstance(Config.BASE_DIR, Path)
        assert isinstance(Config.DATA_DIR, Path)
        assert isinstance(Config.LOGS_DIR, Path)
        assert isinstance(Config.DB_PATH, Path)

    def test_ui_dimensions(self):
        """Test UI dimension constants"""
        assert Config.WINDOW_WIDTH == 1400
        assert Config.WINDOW_HEIGHT == 900
        assert Config.WINDOW_MIN_WIDTH == 1024
        assert Config.WINDOW_MIN_HEIGHT == 768
        assert Config.LEFT_PANEL_WIDTH == 200
        assert Config.RIGHT_PANEL_WIDTH == 250

    def test_calibration_constants(self):
        """Test calibration constants"""
        assert Config.CARD_WIDTH_CM == 8.5
        assert Config.CARD_HEIGHT_CM == 5.4
        assert Config.MIN_CALIBRATION_PIXELS == 10
        assert Config.MAX_CALIBRATION_PIXELS == 10000
        assert Config.MAX_PERSPECTIVE_DISTORTION == 0.3

    def test_image_settings(self):
        """Test image processing settings"""
        assert '.png' in Config.ALLOWED_IMAGE_EXTENSIONS
        assert '.jpg' in Config.ALLOWED_IMAGE_EXTENSIONS
        assert '.jpeg' in Config.ALLOWED_IMAGE_EXTENSIONS
        assert '.bmp' in Config.ALLOWED_IMAGE_EXTENSIONS
        assert Config.MAX_IMAGE_SIZE_MB == 50
        assert Config.MAX_IMAGE_SIZE_BYTES == 50 * 1024 * 1024

    def test_profile_settings(self):
        """Test profile validation settings"""
        assert Config.MAX_PROFILE_NAME_LENGTH == 50
        assert 'coder' in Config.VALID_ROLES
        assert 'artist' in Config.VALID_ROLES
        assert 'gamer' in Config.VALID_ROLES
        assert 'admin' in Config.VALID_ROLES
        assert 'left' in Config.VALID_HANDEDNESS
        assert 'right' in Config.VALID_HANDEDNESS

    def test_ergonomic_scoring(self):
        """Test ergonomic scoring thresholds"""
        assert Config.SCORE_EXCELLENT_THRESHOLD == 80
        assert Config.SCORE_GOOD_THRESHOLD == 60
        assert Config.PRIORITY_1_PENALTY == 60
        assert Config.PRIORITY_2_PENALTY == 40
        assert Config.PRIORITY_3_PENALTY == 20

    def test_is_valid_image_extension(self):
        """Test image extension validation"""
        assert Config.is_valid_image_extension("test.png") is True
        assert Config.is_valid_image_extension("test.jpg") is True
        assert Config.is_valid_image_extension("test.PNG") is True  # Case insensitive
        assert Config.is_valid_image_extension("test.txt") is False
        assert Config.is_valid_image_extension("test.pdf") is False

    def test_is_valid_role(self):
        """Test role validation"""
        assert Config.is_valid_role("coder") is True
        assert Config.is_valid_role("Coder") is True  # Case insensitive
        assert Config.is_valid_role("ARTIST") is True
        assert Config.is_valid_role("invalid") is False
        assert Config.is_valid_role("developer") is False

    def test_is_valid_handedness(self):
        """Test handedness validation"""
        assert Config.is_valid_handedness("left") is True
        assert Config.is_valid_handedness("right") is True
        assert Config.is_valid_handedness("LEFT") is True  # Case insensitive
        assert Config.is_valid_handedness("ambidextrous") is False
        assert Config.is_valid_handedness("middle") is False

    def test_get_score_color(self):
        """Test score color mapping"""
        assert Config.get_score_color(100) == "green"
        assert Config.get_score_color(85) == "green"
        assert Config.get_score_color(80) == "green"
        assert Config.get_score_color(75) == "orange"
        assert Config.get_score_color(60) == "orange"
        assert Config.get_score_color(55) == "red"
        assert Config.get_score_color(0) == "red"

    def test_get_db_path(self):
        """Test database path getter"""
        db_path = Config.get_db_path()
        assert isinstance(db_path, str)
        assert db_path.endswith("deskopt.db")

    def test_get_log_path(self):
        """Test log path getter"""
        log_path = Config.get_log_path()
        assert isinstance(log_path, str)
        assert log_path.endswith("deskopt.log")

    def test_ensure_directories(self):
        """Test directory creation"""
        # This should not raise any errors
        Config.ensure_directories()
        assert Config.DATA_DIR.exists()
        assert Config.LOGS_DIR.exists()
        assert Config.MODELS_DIR.exists()
