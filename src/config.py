"""
Configuration file for DeskOpt application
Centralizes all hard-coded values for easy maintenance
"""
import os
from pathlib import Path


class Config:
    """Application configuration"""

    # Application Info
    APP_NAME = "DeskOpt - AI Ergonomics Engine"
    VERSION = "1.0.0"

    # Paths
    BASE_DIR = Path(__file__).parent.parent.absolute()
    DATA_DIR = (BASE_DIR / "data").absolute()
    LOGS_DIR = (BASE_DIR / "logs").absolute()
    MODELS_DIR = (BASE_DIR / "models").absolute()

    # Database
    DB_NAME = "deskopt.db"
    DB_PATH = (DATA_DIR / DB_NAME).absolute()

    # Logging
    LOG_FILE = "deskopt.log"
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # UI Settings
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    WINDOW_MIN_WIDTH = 1024
    WINDOW_MIN_HEIGHT = 768

    LEFT_PANEL_WIDTH = 200
    RIGHT_PANEL_WIDTH = 250
    PROGRESS_BAR_WIDTH = 200

    # Calibration
    CARD_WIDTH_CM = 8.5  # Standard credit card width
    CARD_HEIGHT_CM = 5.4  # Standard credit card height
    MIN_CALIBRATION_PIXELS = 10  # Minimum pixel distance for calibration
    MAX_CALIBRATION_PIXELS = 10000  # Maximum pixel distance for calibration
    MAX_PERSPECTIVE_DISTORTION = 0.3  # 30% maximum difference between X and Y scales

    # Image Processing
    ALLOWED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp']
    MAX_IMAGE_SIZE_MB = 50  # Maximum image file size in MB
    MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

    # YOLO Model
    YOLO_MODEL_NAME = "yolov8m.pt"  # medium version for better accuracy
    YOLO_CONFIDENCE_THRESHOLD = 0.7  # Higher threshold = fewer false positives
    YOLO_IOU_THRESHOLD = 0.45

    # Profile
    MAX_PROFILE_NAME_LENGTH = 50
    PROFILE_NAME_PATTERN = r'^[a-zA-Z0-9\s\-_.]+$'
    VALID_ROLES = ['coder', 'artist', 'gamer', 'admin']
    VALID_HANDEDNESS = ['left', 'right']

    # Ergonomics
    SCORE_EXCELLENT_THRESHOLD = 80  # Score >= 80 is excellent (green)
    SCORE_GOOD_THRESHOLD = 60  # Score >= 60 is good (orange)
    # Score < 60 is poor (red)

    PRIORITY_1_PENALTY = 60  # High priority violations
    PRIORITY_2_PENALTY = 40  # Medium priority violations
    PRIORITY_3_PENALTY = 20  # Low priority violations

    # Analysis Worker
    WORKER_TIMEOUT_MS = 120000  # 2 minutes timeout for analysis

    # Status Messages
    MSG_READY = "Ready - Import an image to begin"
    MSG_IMAGE_LOADED = "Image loaded successfully"
    MSG_CALIBRATION_COMPLETE = "Calibration complete"
    MSG_DESK_MARKED = "Desk edges marked"
    MSG_ANALYSIS_COMPLETE = "Analysis complete!"
    MSG_ANALYSIS_FAILED = "Analysis failed"

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        cls.DATA_DIR.mkdir(exist_ok=True, parents=True)
        cls.LOGS_DIR.mkdir(exist_ok=True, parents=True)
        cls.MODELS_DIR.mkdir(exist_ok=True, parents=True)

    @classmethod
    def get_db_path(cls):
        """Get database path as string"""
        return str(cls.DB_PATH)

    @classmethod
    def get_log_path(cls):
        """Get log file path as string"""
        return str(cls.LOGS_DIR / cls.LOG_FILE)

    @classmethod
    def is_valid_image_extension(cls, file_path):
        """Check if file has a valid image extension"""
        from pathlib import Path
        return Path(file_path).suffix.lower() in cls.ALLOWED_IMAGE_EXTENSIONS

    @classmethod
    def is_valid_role(cls, role):
        """Check if role is valid"""
        return role.lower() in cls.VALID_ROLES

    @classmethod
    def is_valid_handedness(cls, handedness):
        """Check if handedness is valid"""
        return handedness.lower() in cls.VALID_HANDEDNESS

    @classmethod
    def get_score_color(cls, score):
        """Get color name based on score"""
        if score >= cls.SCORE_EXCELLENT_THRESHOLD:
            return "green"
        elif score >= cls.SCORE_GOOD_THRESHOLD:
            return "orange"
        else:
            return "red"


# Initialize directories on module import
Config.ensure_directories()
