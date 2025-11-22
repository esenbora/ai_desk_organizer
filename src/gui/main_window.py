import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QComboBox, 
                            QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                            QTabWidget, QTextEdit, QSplitter, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QPen, QFont, QColor, QImage
import cv2
import numpy as np

from core.database import DatabaseManager
from core.calibration import CalibrationManager
from ai.mock_detector import MockObjectDetector as ObjectDetector
from core.ergonomics import ErgonomicEngine

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
        self.mode = 'view'  # 'view', 'calibration', 'desk', 'review'
        self.scale_factor = 1.0
        self.original_width = 0
        self.original_height = 0
        
    def set_image(self, image_path):
        """Load and display an image"""
        # Load image with OpenCV for processing
        self.image = cv2.imread(image_path)
        
        # Load image directly with QPixmap for display
        self.original_pixmap = QPixmap(image_path)
        
        if self.original_pixmap.isNull():
            print(f"Failed to load image: {image_path}")
            return
            
        # Get image dimensions
        w = self.original_pixmap.width()
        h = self.original_pixmap.height()
        
        print(f"Image loaded: {w}x{h}")
        
        # Store original size and reset scaling
        self.original_width = w
        self.original_height = h
        self.scale_factor = 1.0
        
        # Trigger resize to fit available space
        self.update_image_scaling()
        self.update()
    
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
        
        # Draw detected items
        if self.detected_items:
            pen = QPen(QColor(0, 0, 255), 2)
            painter.setPen(pen)
            for item in self.detected_items:
                x = int(item['x'] * self.scale_factor)
                y = int(item['y'] * self.scale_factor)
                w = int(item['width'] * self.scale_factor)
                h = int(item['height'] * self.scale_factor)
                painter.drawRect(x-w//2, y-h//2, w, h)
                painter.drawText(x-w//2, y-h//2-5, item['slug'])
    
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
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("DeskOpt - AI Ergonomics Engine")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Left panel - Controls (fixed width)
        left_panel = self.create_control_panel()
        left_panel.setFixedWidth(200)
        main_layout.addWidget(left_panel)
        
        # Center - Image display (fits to available space)
        self.image_widget = ImageWidget()
        self.image_widget.point_clicked.connect(self.handle_image_click)
        main_layout.addWidget(self.image_widget, 1)
        
        # Right panel - Results (fixed width)
        right_panel = self.create_results_panel()
        right_panel.setFixedWidth(250)
        main_layout.addWidget(right_panel)
        
        # Status bar
        self.statusBar().showMessage("Ready - Import an image to begin")
        
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
        
        layout.addStretch()
        return panel
    
    def create_results_panel(self):
        """Create the results panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Tab widget for different results
        self.results_tabs = QTabWidget()
        
        # Detected items tab
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Item", "Position", "Confidence", "Action"])
        self.results_tabs.addTab(self.items_table, "Detected Items")
        
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
            name = name_input.text().strip()
            if name:
                role = role_input.currentText().lower()
                handedness = hand_input.currentText().lower()
                profile_id = self.db.create_profile(name, role, handedness)
                self.load_profiles()
                self.profile_combo.setCurrentIndex(self.profile_combo.count() - 1)
                dialog.accept()
        
        save_btn.clicked.connect(save_profile)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
    
    def import_image(self):
        """Import a desk photo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Desk Photo", "", "Image Files (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.image_widget.set_image(file_path)
            self.image_widget.set_mode('view')
            
            # Update status bar with image info
            import os
            filename = os.path.basename(file_path)
            
            # Get image info for debugging
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.statusBar().showMessage(f"Loaded: {filename} ({pixmap.width()}x{pixmap.height()}) - Scale: {self.image_widget.scale_factor:.2f}")
            else:
                self.statusBar().showMessage(f"Failed to load: {filename}")
                QMessageBox.warning(self, "Error", f"Could not load image: {filename}")
    
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
        """Analyze the desk setup"""
        if not self.current_image_path:
            QMessageBox.warning(self, "Warning", "Please import an image first")
            return
        
        if self.calibration.scale_factor is None:
            QMessageBox.warning(self, "Warning", "Please complete calibration first")
            return
        
        if not self.calibration.is_desk_complete():
            QMessageBox.warning(self, "Warning", "Please mark desk edges first")
            return
        
        # Detect objects
        detected_items = self.detector.detect_objects(self.current_image_path)
        
        # Transform to desk coordinates
        processed_items = []
        for item in detected_items:
            x_cm, y_cm = self.calibration.transform_to_desk_coordinates(item['x'], item['y'])
            if x_cm is not None:
                processed_items.append({
                    'item_slug': item['slug'],
                    'x_pos': x_cm,
                    'y_pos': y_cm,
                    'width': self.calibration.pixels_to_cm(item['width']),
                    'height': self.calibration.pixels_to_cm(item['height']),
                    'confidence': item['confidence']
                })
        
        # Get profile info
        profile_id = self.profile_combo.currentData()
        if not profile_id:
            QMessageBox.warning(self, "Warning", "Please select or create a profile")
            return
        
        # Save scan
        desk_bounds = self.calibration.get_desk_bounds_json()
        self.current_scan_id = self.db.save_scan(
            profile_id, self.current_image_path, 
            self.calibration.scale_factor, desk_bounds
        )
        
        # Save detected items
        self.db.save_detected_items(self.current_scan_id, processed_items)
        
        # Analyze ergonomics
        role = self.role_combo.currentText().lower()
        handedness = self.handedness_combo.currentText().lower()
        desk_width_cm, desk_height_cm = self.calibration.get_desk_dimensions_cm()
        analysis = self.ergonomic_engine.analyze_ergonomics(
            self.current_scan_id, role, desk_width_cm, desk_height_cm, handedness
        )
        
        # Display results
        self.display_results(processed_items, analysis)
        
        # Show detected items on image (convert back to pixel coordinates for display)
        display_items = []
        for item in detected_items:
            display_items.append({
                'x': item['x'],
                'y': item['y'], 
                'width': item['width'],
                'height': item['height'],
                'slug': item['slug']
            })
        self.image_widget.set_detected_items(display_items)
    
    def display_results(self, items, analysis):
        """Display analysis results"""
        # Update items table
        self.items_table.setRowCount(len(items))
        for i, item in enumerate(items):
            self.items_table.setItem(i, 0, QTableWidgetItem(item['item_slug']))
            self.items_table.setItem(i, 1, QTableWidgetItem(f"({item['x_pos']:.1f}, {item['y_pos']:.1f})"))
            self.items_table.setItem(i, 2, QTableWidgetItem(f"{item['confidence']:.2f}"))
            self.items_table.setItem(i, 3, QTableWidgetItem("Keep"))
        
        # Update recommendations
        recommendations_text = ""
        for rec in analysis['recommendations']:
            recommendations_text += f"• {rec['item']}: {rec['advice']}\n"
            recommendations_text += f"  Move from ({rec['current_pos'][0]:.1f}, {rec['current_pos'][1]:.1f}) "
            recommendations_text += f"to ({rec['optimal_pos'][0]:.1f}, {rec['optimal_pos'][1]:.1f})\n\n"
        
        self.recommendations_text.setPlainText(recommendations_text or "No recommendations - Great setup!")
        
        # Update score
        self.score_label.setText(f"Ergonomic Score: {analysis['score']}/100")
        
        # Color code the score
        if analysis['score'] >= 80:
            color = "green"
        elif analysis['score'] >= 60:
            color = "orange"
        else:
            color = "red"
        self.score_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")

def main():
    app = QApplication(sys.argv)
    window = DeskOptMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()