import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QPushButton, QComboBox,
                            QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                            QTabWidget, QTextEdit, QSplitter, QFrame, QProgressBar,
                            QHeaderView, QAbstractItemView, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QPen, QFont, QColor, QImage
import cv2
import numpy as np

from config import Config
from core.database import DatabaseManager
from core.calibration import CalibrationManager
from ai.detector import ObjectDetector
from core.ergonomics import ErgonomicEngine
from gui.analysis_worker import AnalysisWorker
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ImageWidget(QWidget):
    """Custom widget for displaying and interacting with images"""
    point_clicked = pyqtSignal(int, int)
    
    def __init__(self):
        super().__init__()
        self.image = None
        self.original_pixmap = None
        self.pixmap = None
        self.calibration_points = []
        self.desk_corners = []
        self.detected_items = []
        self.recommendations = []  # Store recommendations for visual overlay
        self.ergonomic_zones = []  # Store zone information
        self.show_overlay = True   # Toggle for showing visual overlays
        self.mode = 'view'  # 'view', 'calibration', 'desk', 'review'
        self.scale_factor = 1.0
        self.original_width = 0
        self.original_height = 0
        
    def set_image(self, image_path):
        """Load and display an image"""
        try:
            # Load image with OpenCV for processing
            self.image = cv2.imread(image_path)
            if self.image is None:
                raise ValueError(f"OpenCV failed to read image: {image_path}")

            # Load image directly with QPixmap for display
            self.original_pixmap = QPixmap(image_path)

            if self.original_pixmap.isNull():
                raise ValueError(f"QPixmap failed to load image: {image_path}")

            # Get image dimensions
            w = self.original_pixmap.width()
            h = self.original_pixmap.height()

            if w <= 0 or h <= 0:
                raise ValueError(f"Invalid image dimensions: {w}x{h}")

            logger.info(f"Image loaded successfully: {w}x{h}")

            # Store original size and reset scaling
            self.original_width = w
            self.original_height = h
            self.scale_factor = 1.0

            # Trigger resize to fit available space
            self.update_image_scaling()
            self.update()

        except Exception as e:
            logger.error(f"Error loading image: {e}", exc_info=True)
            self.original_pixmap = None
            self.image = None
            raise
    
    def set_mode(self, mode):
        """Set interaction mode"""
        self.mode = mode
        if mode == 'calibration':
            self.calibration_points = []
        elif mode == 'desk':
            self.desk_corners = []
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse clicks"""
        if self.pixmap and event.button() == Qt.MouseButton.LeftButton:
            if self.mode in ['calibration', 'desk']:
                # Calculate offset for centered image
                x_offset = (self.width() - self.pixmap.width()) // 2
                y_offset = (self.height() - self.pixmap.height()) // 2
                
                # Get click position relative to image
                click_x = event.position().x() - x_offset
                click_y = event.position().y() - y_offset
                
                # Check if click is within image bounds
                if (0 <= click_x <= self.pixmap.width() and 
                    0 <= click_y <= self.pixmap.height()):
                    # Convert to original image coordinates
                    x = click_x / self.scale_factor
                    y = click_y / self.scale_factor
                    self.point_clicked.emit(int(x), int(y))
    
    def add_calibration_point(self, x, y):
        """Add a calibration point"""
        self.calibration_points.append((x, y))
        self.update()
    
    def add_desk_corner(self, x, y):
        """Add a desk corner"""
        self.desk_corners.append((x, y))
        self.update()
    
    def set_detected_items(self, items):
        """Set detected items for display"""
        self.detected_items = items
        self.update()

    def set_recommendations(self, recommendations):
        """Set recommendations for visual overlay"""
        self.recommendations = recommendations
        self.update()

    def set_ergonomic_zones(self, zones):
        """Set ergonomic zones for visual overlay"""
        self.ergonomic_zones = zones
        self.update()

    def toggle_overlay(self, show):
        """Toggle visual overlay display"""
        self.show_overlay = show
        self.update()

    def draw_ergonomic_zones(self, painter):
        """Draw ergonomic zones (optimal, acceptable, poor)"""
        if not self.ergonomic_zones:
            return

        for zone in self.ergonomic_zones:
            zone_type = zone.get('type', 'optimal')
            x = int(zone['x'] * self.scale_factor)
            y = int(zone['y'] * self.scale_factor)
            width = int(zone['width'] * self.scale_factor)
            height = int(zone['height'] * self.scale_factor)

            # Color based on zone type
            if zone_type == 'optimal':
                color = QColor(0, 255, 0, 50)  # Green, semi-transparent
            elif zone_type == 'acceptable':
                color = QColor(255, 255, 0, 50)  # Yellow
            else:
                color = QColor(255, 0, 0, 50)  # Red

            painter.fillRect(x, y, width, height, color)
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue()), 2))
            painter.drawRect(x, y, width, height)

            # Draw zone label
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(x + 5, y + 15, zone_type.upper())

    def draw_ergonomic_overlays(self, painter):
        """Draw ergonomic zone overlays"""
        # Calculate ergonomic zones based on desk dimensions
        if not self.desk_corners or len(self.desk_corners) < 4:
            return

        # Get desk bounds
        desk_xs = [c[0] for c in self.desk_corners]
        desk_ys = [c[1] for c in self.desk_corners]
        min_x, max_x = min(desk_xs), max(desk_xs)
        min_y, max_y = min(desk_ys), max(desk_ys)
        desk_width = max_x - min_x
        desk_height = max_y - min_y

        # Primary reach zone (40cm from front edge) - GREEN
        primary_zone_depth = min(desk_height * 0.4, 40 * 10)  # Assume ~10 pixels per cm
        zone_y = max_y - primary_zone_depth
        painter.fillRect(
            int(min_x * self.scale_factor),
            int(zone_y * self.scale_factor),
            int(desk_width * self.scale_factor),
            int(primary_zone_depth * self.scale_factor),
            QColor(0, 255, 0, 30)
        )
        painter.setPen(QPen(QColor(0, 200, 0), 2, Qt.PenStyle.DashLine))
        painter.drawLine(
            int(min_x * self.scale_factor),
            int(zone_y * self.scale_factor),
            int(max_x * self.scale_factor),
            int(zone_y * self.scale_factor)
        )

        # Draw zone label
        painter.setPen(QPen(QColor(0, 150, 0), 1))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            int((min_x + 10) * self.scale_factor),
            int((zone_y + 15) * self.scale_factor),
            "PRIMARY REACH ZONE"
        )

        # Secondary reach zone - YELLOW
        secondary_zone_start = zone_y - primary_zone_depth * 0.5
        if secondary_zone_start > min_y:
            painter.fillRect(
                int(min_x * self.scale_factor),
                int(secondary_zone_start * self.scale_factor),
                int(desk_width * self.scale_factor),
                int(primary_zone_depth * 0.5 * self.scale_factor),
                QColor(255, 255, 0, 20)
            )
            painter.setPen(QPen(QColor(200, 200, 0), 2, Qt.PenStyle.DashLine))
            painter.drawLine(
                int(min_x * self.scale_factor),
                int(secondary_zone_start * self.scale_factor),
                int(max_x * self.scale_factor),
                int(secondary_zone_start * self.scale_factor)
            )

    def draw_item_bbox(self, painter, item):
        """Draw enhanced bounding box for detected item"""
        x = int(item['x'] * self.scale_factor)
        y = int(item['y'] * self.scale_factor)
        w = int(item['width'] * self.scale_factor)
        h = int(item['height'] * self.scale_factor)

        # Draw bounding box
        pen = QPen(QColor(0, 150, 255), 2)
        painter.setPen(pen)
        painter.drawRect(x-w//2, y-h//2, w, h)

        # Draw item label with background
        label = item['slug'].upper()
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)

        # Calculate label dimensions
        metrics = painter.fontMetrics()
        label_width = metrics.horizontalAdvance(label) + 8
        label_height = metrics.height() + 4

        # Draw label background
        label_x = x - w//2
        label_y = y - h//2 - label_height - 2
        painter.fillRect(label_x, label_y, label_width, label_height, QColor(0, 150, 255))

        # Draw label text
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(label_x + 4, label_y + label_height - 4, label)

    def draw_recommendation_arrows(self, painter):
        """Draw arrows showing where items should move"""
        for rec in self.recommendations:
            if 'current_pos' not in rec or 'optimal_pos' not in rec:
                continue

            # Get current and optimal positions
            curr_x = int(rec['current_pos'][0] * 10 * self.scale_factor)  # Convert cm to pixels
            curr_y = int(rec['current_pos'][1] * 10 * self.scale_factor)
            opt_x = int(rec['optimal_pos'][0] * 10 * self.scale_factor)
            opt_y = int(rec['optimal_pos'][1] * 10 * self.scale_factor)

            # Draw arrow from current to optimal position
            painter.setPen(QPen(QColor(255, 100, 0), 3))
            painter.drawLine(curr_x, curr_y, opt_x, opt_y)

            # Draw arrowhead
            angle = np.arctan2(opt_y - curr_y, opt_x - curr_x)
            arrow_size = 15

            # Arrow tip points
            tip_x = opt_x
            tip_y = opt_y
            left_x = tip_x - arrow_size * np.cos(angle - np.pi/6)
            left_y = tip_y - arrow_size * np.sin(angle - np.pi/6)
            right_x = tip_x - arrow_size * np.cos(angle + np.pi/6)
            right_y = tip_y - arrow_size * np.sin(angle + np.pi/6)

            painter.drawLine(int(tip_x), int(tip_y), int(left_x), int(left_y))
            painter.drawLine(int(tip_x), int(tip_y), int(right_x), int(right_y))

            # Draw distance label
            distance = np.sqrt((opt_x - curr_x)**2 + (opt_y - curr_y)**2) / (10 * self.scale_factor)
            if distance > 1:  # Only show if movement > 1cm
                mid_x = (curr_x + opt_x) // 2
                mid_y = (curr_y + opt_y) // 2

                label = f"{distance:.1f}cm"
                font = QFont()
                font.setPointSize(8)
                font.setBold(True)
                painter.setFont(font)

                # Label background
                metrics = painter.fontMetrics()
                label_width = metrics.horizontalAdvance(label) + 6
                label_height = metrics.height() + 2
                painter.fillRect(mid_x - label_width//2, mid_y - label_height//2,
                               label_width, label_height, QColor(255, 255, 255, 200))

                # Label text
                painter.setPen(QPen(QColor(255, 100, 0), 1))
                painter.drawText(mid_x - label_width//2 + 3, mid_y + label_height//2 - 2, label)

    def paintEvent(self, event):
        """Draw the image and overlays"""
        if not self.pixmap:
            return
        
        painter = QPainter(self)
        
        # Center the scaled image
        x_offset = (self.width() - self.pixmap.width()) // 2
        y_offset = (self.height() - self.pixmap.height()) // 2
        
        painter.drawPixmap(x_offset, y_offset, self.pixmap)
        
        # Adjust coordinate system for centered image
        painter.translate(x_offset, y_offset)
        
        # Draw calibration points
        if self.calibration_points:
            pen = QPen(QColor(255, 0, 0), 3)
            painter.setPen(pen)
            for i, point in enumerate(self.calibration_points):
                x, y = int(point[0] * self.scale_factor), int(point[1] * self.scale_factor)
                painter.drawEllipse(x-5, y-5, 10, 10)
                painter.drawText(x+10, y-10, f"{i+1}")
        
        # Draw desk corners
        if self.desk_corners:
            pen = QPen(QColor(0, 255, 0), 3)
            painter.setPen(pen)
            for i, corner in enumerate(self.desk_corners):
                x, y = int(corner[0] * self.scale_factor), int(corner[1] * self.scale_factor)
                painter.drawEllipse(x-5, y-5, 10, 10)
                painter.drawText(x+10, y-10, f"Desk {i+1}")
            
            # Draw desk outline
            if len(self.desk_corners) == 4:
                pen = QPen(QColor(0, 255, 0), 2)
                painter.setPen(pen)
                for i in range(4):
                    next_i = (i + 1) % 4
                    x1, y1 = int(self.desk_corners[i][0] * self.scale_factor), int(self.desk_corners[i][1] * self.scale_factor)
                    x2, y2 = int(self.desk_corners[next_i][0] * self.scale_factor), int(self.desk_corners[next_i][1] * self.scale_factor)
                    painter.drawLine(x1, y1, x2, y2)
        
        # Draw visual overlays (if enabled)
        if self.show_overlay and self.mode == 'view':
            self.draw_ergonomic_overlays(painter)

        # Draw detected items with enhanced bounding boxes
        if self.detected_items:
            for item in self.detected_items:
                self.draw_item_bbox(painter, item)

        # Draw recommendation arrows
        if self.show_overlay and self.recommendations:
            self.draw_recommendation_arrows(painter)
    
    def update_image_scaling(self):
        """Update image scaling to fit available space"""
        if not self.original_pixmap:
            return
            
        # Get available space (widget size)
        available_width = self.width()
        available_height = self.height()
        
        # Calculate scale factor to fit image in available space
        scale_x = available_width / self.original_width
        scale_y = available_height / self.original_height
        self.scale_factor = min(scale_x, scale_y, 1.0)  # Don't upscale
        
        # Scale the pixmap
        if self.scale_factor == 1.0:
            self.pixmap = self.original_pixmap
        else:
            scaled_width = int(self.original_width * self.scale_factor)
            scaled_height = int(self.original_height * self.scale_factor)
            self.pixmap = self.original_pixmap.scaled(
                scaled_width, scaled_height, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
    
    def resizeEvent(self, event):
        """Handle widget resize"""
        super().resizeEvent(event)
        self.update_image_scaling()
        self.update()

class DeskOptMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.calibration = CalibrationManager()
        self.detector = ObjectDetector()
        self.ergonomic_engine = ErgonomicEngine(self.db)

        self.current_image_path = None
        self.current_profile = None
        self.current_scan_id = None

        # Worker thread for background analysis
        self.analysis_worker = None
        self.is_analyzing = False

        # Manual item corrections
        self.detected_items_data = []  # Store full item data for editing
        self.manual_corrections = {}   # Track user edits {row: {field: value}}

        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(Config.APP_NAME)
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        self.setMinimumSize(Config.WINDOW_MIN_WIDTH, Config.WINDOW_MIN_HEIGHT)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left panel - Controls (fixed width)
        left_panel = self.create_control_panel()
        left_panel.setFixedWidth(Config.LEFT_PANEL_WIDTH)
        main_layout.addWidget(left_panel)

        # Center - Image display (fits to available space)
        self.image_widget = ImageWidget()
        self.image_widget.point_clicked.connect(self.handle_image_click)
        main_layout.addWidget(self.image_widget, 1)

        # Right panel - Results (fixed width)
        right_panel = self.create_results_panel()
        right_panel.setFixedWidth(Config.RIGHT_PANEL_WIDTH)
        main_layout.addWidget(right_panel)

        # Status bar with progress bar
        self.statusBar().showMessage(Config.MSG_READY)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedWidth(Config.PROGRESS_BAR_WIDTH)
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
    def create_control_panel(self):
        """Create the control panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Profile section
        profile_group = QFrame()
        profile_layout = QVBoxLayout(profile_group)
        profile_layout.addWidget(QLabel("Profile:"))
        
        self.profile_combo = QComboBox()
        self.load_profiles()
        profile_layout.addWidget(self.profile_combo)
        
        # New profile button
        new_profile_btn = QPushButton("New Profile")
        new_profile_btn.clicked.connect(self.create_new_profile)
        profile_layout.addWidget(new_profile_btn)
        
        layout.addWidget(profile_group)
        
        # Context section
        context_group = QFrame()
        context_layout = QVBoxLayout(context_group)
        context_layout.addWidget(QLabel("Your Setup:"))
        
        # Role selection
        context_layout.addWidget(QLabel("Role:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Coder", "Artist", "Gamer", "Admin"])
        self.role_combo.setCurrentText("Coder")
        context_layout.addWidget(self.role_combo)
        
        # Handedness selection
        context_layout.addWidget(QLabel("Handedness:"))
        self.handedness_combo = QComboBox()
        self.handedness_combo.addItems(["Right", "Left"])
        self.handedness_combo.setCurrentText("Right")
        context_layout.addWidget(self.handedness_combo)
        
        layout.addWidget(context_group)
        
        # Image import
        import_btn = QPushButton("Import Desk Photo")
        import_btn.clicked.connect(self.import_image)
        layout.addWidget(import_btn)
        
        # Calibration section
        calib_group = QFrame()
        calib_layout = QVBoxLayout(calib_group)
        calib_layout.addWidget(QLabel("Calibration:"))
        
        self.calib_btn = QPushButton("Calibrate with Card")
        self.calib_btn.clicked.connect(self.start_calibration)
        calib_layout.addWidget(self.calib_btn)
        
        self.desk_btn = QPushButton("Mark Desk Edges")
        self.desk_btn.clicked.connect(self.start_desk_marking)
        calib_layout.addWidget(self.desk_btn)
        
        layout.addWidget(calib_group)
        
        # Analysis
        analyze_btn = QPushButton("Analyze Setup")
        analyze_btn.clicked.connect(self.analyze_setup)
        layout.addWidget(analyze_btn)

        # Visual overlay toggle
        self.overlay_checkbox = QCheckBox("Show Visual Overlays")
        self.overlay_checkbox.setChecked(True)
        self.overlay_checkbox.stateChanged.connect(
            lambda state: self.image_widget.toggle_overlay(state == Qt.CheckState.Checked.value)
        )
        layout.addWidget(self.overlay_checkbox)

        layout.addStretch()
        return panel
    
    def create_results_panel(self):
        """Create the results panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Tab widget for different results
        self.results_tabs = QTabWidget()
        
        # Detected items tab with manual correction
        items_widget = QWidget()
        items_layout = QVBoxLayout(items_widget)

        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Type", "Position", "Confidence", "Status", "Action"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        items_layout.addWidget(self.items_table)

        # Correction buttons
        correction_layout = QHBoxLayout()

        add_item_btn = QPushButton("Add Item")
        add_item_btn.clicked.connect(self.add_manual_item)
        correction_layout.addWidget(add_item_btn)

        reanalyze_btn = QPushButton("Re-analyze with Corrections")
        reanalyze_btn.clicked.connect(self.reanalyze_with_corrections)
        correction_layout.addWidget(reanalyze_btn)

        items_layout.addLayout(correction_layout)

        self.results_tabs.addTab(items_widget, "Detected Items")
        
        # Recommendations tab
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        self.results_tabs.addTab(self.recommendations_text, "Recommendations")
        
        # Score tab
        self.score_label = QLabel("Ergonomic Score: --")
        self.score_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        score_widget = QWidget()
        score_layout = QVBoxLayout(score_widget)
        score_layout.addWidget(self.score_label)
        score_layout.addStretch()
        self.results_tabs.addTab(score_widget, "Score")
        
        layout.addWidget(self.results_tabs)
        return panel
    
    def load_profiles(self):
        """Load user profiles"""
        profiles = self.db.get_profiles()
        self.profile_combo.clear()
        for profile in profiles:
            self.profile_combo.addItem(profile[1], profile[0])  # name, id
    
    def create_new_profile(self):
        """Create a new user profile"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Profile")
        layout = QVBoxLayout(dialog)
        
        # Name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_input = QLineEdit()
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)
        
        # Role selection
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel("Role:"))
        role_input = QComboBox()
        role_input.addItems(["Coder", "Artist", "Gamer", "Admin"])
        role_layout.addWidget(role_input)
        layout.addLayout(role_layout)
        
        # Handedness selection
        hand_layout = QHBoxLayout()
        hand_layout.addWidget(QLabel("Handedness:"))
        hand_input = QComboBox()
        hand_input.addItems(["Right", "Left"])
        hand_layout.addWidget(hand_input)
        layout.addLayout(hand_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        def save_profile():
            try:
                name = name_input.text().strip()
                if not name:
                    QMessageBox.warning(dialog, "Invalid Input", "Please enter a profile name.")
                    return

                # Validate name length
                if len(name) > Config.MAX_PROFILE_NAME_LENGTH:
                    QMessageBox.warning(
                        dialog, "Invalid Input",
                        f"Profile name must be {Config.MAX_PROFILE_NAME_LENGTH} characters or less."
                    )
                    return

                # Validate name characters (alphanumeric, spaces, and basic punctuation)
                import re
                if not re.match(Config.PROFILE_NAME_PATTERN, name):
                    QMessageBox.warning(
                        dialog, "Invalid Input",
                        "Profile name can only contain letters, numbers, spaces, hyphens, underscores, and periods."
                    )
                    return

                role = role_input.currentText().lower()
                handedness = hand_input.currentText().lower()

                logger.info(f"Creating new profile: {name}, role={role}, handedness={handedness}")
                profile_id = self.db.create_profile(name, role, handedness)
                self.load_profiles()
                self.profile_combo.setCurrentIndex(self.profile_combo.count() - 1)
                dialog.accept()
                QMessageBox.information(
                    dialog, "Success",
                    f"Profile '{name}' created successfully!"
                )
            except Exception as e:
                logger.error(f"Failed to create profile: {e}", exc_info=True)
                QMessageBox.critical(
                    dialog, "Error",
                    f"Failed to create profile:\n\n{str(e)}"
                )
        
        save_btn.clicked.connect(save_profile)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def import_image(self):
        """Import a desk photo"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Desk Photo", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
            )

            if not file_path:
                return

            # Validate file exists
            import os
            from pathlib import Path

            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"File does not exist: {file_path}")

            # Validate file extension
            if not Config.is_valid_image_extension(file_path):
                raise ValueError(
                    f"Invalid file type. Please use: {', '.join(Config.ALLOWED_IMAGE_EXTENSIONS)}"
                )

            # Validate file size
            file_size = os.path.getsize(file_path)
            if file_size > Config.MAX_IMAGE_SIZE_BYTES:
                raise ValueError(
                    f"File too large ({file_size / 1024 / 1024:.1f}MB). "
                    f"Maximum size is {Config.MAX_IMAGE_SIZE_MB}MB."
                )

            logger.info(f"Importing image: {file_path}")

            # Try to load the image
            self.current_image_path = file_path
            self.image_widget.set_image(file_path)
            self.image_widget.set_mode('view')

            # Update status bar with image info
            filename = os.path.basename(file_path)
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.statusBar().showMessage(
                    f"Loaded: {filename} ({pixmap.width()}x{pixmap.height()}) - "
                    f"Scale: {self.image_widget.scale_factor:.2f}"
                )
                logger.info(f"Image imported successfully: {filename}")
            else:
                raise ValueError("Failed to create pixmap from image")

        except Exception as e:
            logger.error(f"Failed to import image: {e}", exc_info=True)
            self.current_image_path = None
            QMessageBox.critical(
                self,
                "Image Import Error",
                f"Failed to load image:\n\n{str(e)}\n\nPlease try a different image."
            )
            self.statusBar().showMessage("Image import failed")
    
    def start_calibration(self):
        """Start card calibration"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please import an image first")
            return
        
        self.image_widget.set_mode('calibration')
        self.calibration.reset_calibration()
        QMessageBox.information(self, "Calibration", 
                               "Click the 4 corners of the credit card in order:\n"
                               "1. Top-left\n2. Top-right\n3. Bottom-right\n4. Bottom-left")
    
    def start_desk_marking(self):
        """Start desk edge marking"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please import an image first")
            return
        
        self.image_widget.set_mode('desk')
        QMessageBox.information(self, "Desk Marking", 
                               "Click the 4 corners of your desk in order:\n"
                               "1. Top-left\n2. Top-right\n3. Bottom-right\n4. Bottom-left")
    
    def handle_image_click(self, x, y):
        """Handle clicks on the image widget"""
        if self.image_widget.mode == 'calibration':
            point_num = self.calibration.add_calibration_point(x, y)
            self.image_widget.add_calibration_point(x, y)
            
            if point_num == 4:
                scale = self.calibration.calculate_scale_factor()
                QMessageBox.information(self, "Calibration Complete", 
                                     f"Scale factor: {scale:.2f} pixels/cm")
                self.image_widget.set_mode('view')
        
        elif self.image_widget.mode == 'desk':
            corner_num = self.calibration.add_desk_corner(x, y)
            self.image_widget.add_desk_corner(x, y)
            
            if corner_num == 4:
                width_cm, height_cm = self.calibration.get_desk_dimensions_cm()
                QMessageBox.information(self, "Desk Marking Complete", 
                                     f"Desk size: {width_cm:.1f} x {height_cm:.1f} cm")
                self.image_widget.set_mode('view')
    
    def analyze_setup(self):
        """Analyze the desk setup using background worker thread"""
        try:
            # Prevent multiple simultaneous analyses
            if self.is_analyzing:
                QMessageBox.warning(
                    self, "Analysis in Progress",
                    "An analysis is already running. Please wait for it to complete."
                )
                return

            # Validation checks
            if not self.current_image_path:
                QMessageBox.warning(
                    self, "No Image",
                    "Please import a desk photo using the 'Import Desk Photo' button first."
                )
                return

            if self.calibration.scale_factor is None:
                QMessageBox.warning(
                    self, "Calibration Required",
                    "Please complete calibration by clicking 'Calibrate with Card' and "
                    "selecting the 4 corners of a credit card in your image."
                )
                return

            if not self.calibration.is_desk_complete():
                QMessageBox.warning(
                    self, "Desk Marking Required",
                    "Please mark your desk edges by clicking 'Mark Desk Edges' and "
                    "selecting the 4 corners of your desk surface."
                )
                return

            profile_id = self.profile_combo.currentData()
            if not profile_id:
                QMessageBox.warning(
                    self, "Profile Required",
                    "Please select an existing profile or create a new one."
                )
                return

            # Prepare parameters for worker thread
            params = {
                'image_path': self.current_image_path,
                'profile_id': profile_id,
                'role': self.role_combo.currentText().lower(),
                'handedness': self.handedness_combo.currentText().lower()
            }

            # Create and configure worker thread
            self.analysis_worker = AnalysisWorker(
                self.detector,
                self.calibration,
                self.db,
                self.ergonomic_engine,
                params
            )

            # Connect signals
            self.analysis_worker.progress.connect(self.on_analysis_progress)
            self.analysis_worker.finished.connect(self.on_analysis_finished)
            self.analysis_worker.error.connect(self.on_analysis_error)

            # Update UI state
            self.is_analyzing = True
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.statusBar().showMessage("Starting analysis...")

            # Start worker thread
            logger.info("Starting background analysis...")
            self.analysis_worker.start()

        except Exception as e:
            logger.error(f"Failed to start analysis: {e}", exc_info=True)
            self.is_analyzing = False
            self.progress_bar.setVisible(False)
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Failed to start analysis:\n\n{str(e)}"
            )

    def on_analysis_progress(self, message, percentage):
        """Handle progress updates from worker thread"""
        self.statusBar().showMessage(message)
        self.progress_bar.setValue(percentage)
        logger.debug(f"Analysis progress: {percentage}% - {message}")

    def on_analysis_finished(self, results):
        """Handle successful completion of analysis"""
        try:
            logger.info("Analysis worker finished successfully")

            # Update state
            self.is_analyzing = False
            self.progress_bar.setVisible(False)
            self.current_scan_id = results['scan_id']

            # Display results
            self.display_results(results['processed_items'], results['analysis'])

            # Show detected items on image
            display_items = []
            for item in results['detected_items']:
                display_items.append({
                    'x': item['x'],
                    'y': item['y'],
                    'width': item['width'],
                    'height': item['height'],
                    'slug': item['slug']
                })
            self.image_widget.set_detected_items(display_items)

            # Update status
            score = results['analysis']['score']
            self.statusBar().showMessage(f"Analysis complete! Ergonomic Score: {score}/100")
            logger.info(f"Analysis completed. Score: {score}")

            # Clean up worker
            if self.analysis_worker:
                self.analysis_worker.deleteLater()
                self.analysis_worker = None

        except Exception as e:
            logger.error(f"Error handling analysis results: {e}", exc_info=True)
            self.on_analysis_error(f"Failed to display results: {str(e)}")

    def on_analysis_error(self, error_message):
        """Handle analysis errors"""
        logger.error(f"Analysis error: {error_message}")

        # Update state
        self.is_analyzing = False
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Analysis failed")

        # Show error to user
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"{error_message}\n\nPlease check the log file for details."
        )

        # Clean up worker
        if self.analysis_worker:
            self.analysis_worker.deleteLater()
            self.analysis_worker = None
    
    def display_results(self, items, analysis):
        """Display analysis results"""
        # Store items data for editing
        self.detected_items_data = items.copy()
        self.manual_corrections = {}

        # Update items table with editable controls
        self.items_table.setRowCount(len(items))

        # Available item types from Config
        item_types = [
            'laptop', 'mouse', 'keyboard', 'monitor', 'phone',
            'notebook', 'cup', 'bottle', 'chair', 'clock'
        ]

        for i, item in enumerate(items):
            # Column 0: Item Type (dropdown)
            type_combo = QComboBox()
            type_combo.addItems(item_types)
            type_combo.setCurrentText(item['item_slug'])
            type_combo.currentTextChanged.connect(
                lambda text, row=i: self.on_item_type_changed(row, text)
            )
            self.items_table.setCellWidget(i, 0, type_combo)

            # Column 1: Position (editable)
            pos_item = QTableWidgetItem(f"({item['x_pos']:.1f}, {item['y_pos']:.1f})")
            self.items_table.setItem(i, 1, pos_item)

            # Column 2: Confidence (read-only)
            conf_item = QTableWidgetItem(f"{item['confidence']:.2f}")
            conf_item.setFlags(conf_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.items_table.setItem(i, 2, conf_item)

            # Column 3: Status (read-only indicator)
            status_item = QTableWidgetItem("Detected")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.items_table.setItem(i, 3, status_item)

            # Column 4: Action (delete button)
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_item(row))
            self.items_table.setCellWidget(i, 4, delete_btn)
        
        # Update recommendations with violation details
        recommendations_text = ""

        # Add violation summary
        violations = analysis.get('violations', [])
        if violations:
            # Group violations by priority
            p1_violations = [v for v in violations if v['priority'] == 1]
            p2_violations = [v for v in violations if v['priority'] == 2]
            p3_violations = [v for v in violations if v['priority'] == 3]

            recommendations_text += "=== ERGONOMIC VIOLATIONS ===\n\n"

            if p1_violations:
                recommendations_text += f"🔴 High Priority ({len(p1_violations)}):\n"
                for v in p1_violations:
                    recommendations_text += f"  • {v['item']}: {v['advice']}\n"
                recommendations_text += "\n"

            if p2_violations:
                recommendations_text += f"🟡 Medium Priority ({len(p2_violations)}):\n"
                for v in p2_violations:
                    recommendations_text += f"  • {v['item']}: {v['advice']}\n"
                recommendations_text += "\n"

            if p3_violations:
                recommendations_text += f"🟢 Low Priority ({len(p3_violations)}):\n"
                for v in p3_violations:
                    recommendations_text += f"  • {v['item']}: {v['advice']}\n"
                recommendations_text += "\n"

            recommendations_text += "=== RECOMMENDED POSITIONS ===\n\n"

        # Add detailed recommendations
        for rec in analysis['recommendations']:
            recommendations_text += f"• {rec['item']}: {rec['advice']}\n"
            recommendations_text += f"  Move from ({rec['current_pos'][0]:.1f}, {rec['current_pos'][1]:.1f}) "
            recommendations_text += f"to ({rec['optimal_pos'][0]:.1f}, {rec['optimal_pos'][1]:.1f})\n\n"

        self.recommendations_text.setPlainText(recommendations_text or "No recommendations - Great setup!")

        # Update score
        self.score_label.setText(f"Ergonomic Score: {analysis['score']}/100")

        # Color code the score
        color = Config.get_score_color(analysis['score'])
        self.score_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")

        # Update visual overlays on image
        self.image_widget.set_recommendations(analysis.get('recommendations', []))
        self.image_widget.set_mode('view')  # Enable overlay display mode

    def on_item_type_changed(self, row, new_type):
        """Handle item type change"""
        if row < len(self.detected_items_data):
            self.detected_items_data[row]['item_slug'] = new_type
            # Update status to show it was modified
            status_item = self.items_table.item(row, 3)
            if status_item:
                status_item.setText("Modified")
                status_item.setForeground(QColor("#FFA500"))  # Orange

    def delete_item(self, row):
        """Mark item for deletion"""
        if row < self.items_table.rowCount():
            # Mark status as deleted
            status_item = self.items_table.item(row, 3)
            if status_item:
                status_item.setText("Deleted")
                status_item.setForeground(QColor("#FF0000"))  # Red

            # Disable the row visually
            for col in range(self.items_table.columnCount()):
                widget = self.items_table.cellWidget(row, col)
                if widget:
                    widget.setEnabled(False)
                item = self.items_table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)

    def add_manual_item(self):
        """Add a manual item to the detection list"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QDoubleSpinBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Manual Item")
        layout = QVBoxLayout(dialog)

        # Item type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Item Type:"))
        type_combo = QComboBox()
        type_combo.addItems([
            'laptop', 'mouse', 'keyboard', 'monitor', 'phone',
            'notebook', 'cup', 'bottle', 'chair', 'clock'
        ])
        type_layout.addWidget(type_combo)
        layout.addLayout(type_layout)

        # X position
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X Position (cm):"))
        x_spin = QDoubleSpinBox()
        x_spin.setRange(0, 200)
        x_spin.setValue(50)
        x_spin.setDecimals(1)
        x_layout.addWidget(x_spin)
        layout.addLayout(x_layout)

        # Y position
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y Position (cm):"))
        y_spin = QDoubleSpinBox()
        y_spin.setRange(0, 200)
        y_spin.setValue(30)
        y_spin.setDecimals(1)
        y_layout.addWidget(y_spin)
        layout.addLayout(y_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Add")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Add new item to detected items
            new_item = {
                'item_slug': type_combo.currentText(),
                'x_pos': x_spin.value(),
                'y_pos': y_spin.value(),
                'confidence': 1.0,  # Manual items have 100% confidence
                'bbox': [0, 0, 100, 100]  # Placeholder bbox
            }
            self.detected_items_data.append(new_item)

            # Add row to table
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)

            # Add widgets to new row
            type_combo_widget = QComboBox()
            type_combo_widget.addItems([
                'laptop', 'mouse', 'keyboard', 'monitor', 'phone',
                'notebook', 'cup', 'bottle', 'chair', 'clock'
            ])
            type_combo_widget.setCurrentText(new_item['item_slug'])
            type_combo_widget.currentTextChanged.connect(
                lambda text, r=row: self.on_item_type_changed(r, text)
            )
            self.items_table.setCellWidget(row, 0, type_combo_widget)

            self.items_table.setItem(row, 1, QTableWidgetItem(f"({new_item['x_pos']:.1f}, {new_item['y_pos']:.1f})"))

            conf_item = QTableWidgetItem(f"{new_item['confidence']:.2f}")
            conf_item.setFlags(conf_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.items_table.setItem(row, 2, conf_item)

            status_item = QTableWidgetItem("Manual")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            status_item.setForeground(QColor("#00AA00"))  # Green
            self.items_table.setItem(row, 3, status_item)

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_item(r))
            self.items_table.setCellWidget(row, 4, delete_btn)

            logger.info(f"Manual item added: {new_item['item_slug']} at ({new_item['x_pos']}, {new_item['y_pos']})")

    def reanalyze_with_corrections(self):
        """Re-run ergonomic analysis with manual corrections"""
        if not self.detected_items_data:
            QMessageBox.warning(self, "No Data", "No items to analyze. Please run detection first.")
            return

        # Filter out deleted items
        corrected_items = []
        for i, item in enumerate(self.detected_items_data):
            if i < self.items_table.rowCount():
                status_item = self.items_table.item(i, 3)
                if status_item and status_item.text() != "Deleted":
                    corrected_items.append(item)

        if not corrected_items:
            QMessageBox.warning(self, "No Items", "All items were deleted. Cannot analyze.")
            return

        try:
            # Re-run ergonomic analysis with corrected items
            logger.info(f"Re-analyzing with {len(corrected_items)} corrected items")

            analysis = self.ergonomic_engine.analyze_workspace(
                corrected_items,
                self.calibration.get_desk_dimensions()
            )

            # Update display with new analysis
            self.display_results(corrected_items, analysis)

            # Save corrected items to database
            if self.current_scan_id:
                for item in corrected_items:
                    self.db.add_detected_item(
                        self.current_scan_id,
                        item['item_slug'],
                        item['x_pos'],
                        item['y_pos'],
                        item['confidence']
                    )

            QMessageBox.information(
                self,
                "Analysis Complete",
                f"Re-analysis completed with manual corrections!\nNew Score: {analysis['score']}/100"
            )
            logger.info(f"Re-analysis complete. New score: {analysis['score']}/100")

        except Exception as e:
            logger.error(f"Re-analysis failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Re-analysis failed: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = DeskOptMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()