"""
Worker thread for background analysis to prevent UI freezing
"""
from PyQt6.QtCore import QThread, pyqtSignal
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AnalysisWorker(QThread):
    """
    Background worker thread for desk analysis
    Prevents UI freezing during long-running operations
    """
    # Signals
    progress = pyqtSignal(str, int)  # message, percentage
    finished = pyqtSignal(dict)  # results
    error = pyqtSignal(str)  # error message

    def __init__(self, detector, calibration, db, ergonomic_engine, params):
        """
        Initialize analysis worker

        Args:
            detector: ObjectDetector instance
            calibration: CalibrationManager instance
            db: DatabaseManager instance
            ergonomic_engine: ErgonomicEngine instance
            params: Dictionary with analysis parameters
        """
        super().__init__()
        self.detector = detector
        self.calibration = calibration
        self.db = db
        self.ergonomic_engine = ergonomic_engine
        self.params = params
        self._is_cancelled = False

    def cancel(self):
        """Request cancellation of the operation"""
        logger.info("Analysis cancellation requested")
        self._is_cancelled = True

    def run(self):
        """Main worker thread execution"""
        try:
            logger.info("Analysis worker thread started")

            # Step 1: Object Detection (40% of work)
            if self._is_cancelled:
                return

            self.progress.emit("Detecting objects in image...", 10)
            detected_items = self.detector.detect_objects(self.params['image_path'])

            if not detected_items:
                self.error.emit(
                    "No desk items were detected in the image. Try:\n"
                    "• Using better lighting\n"
                    "• Taking a clearer photo\n"
                    "• Ensuring items are visible and not obscured"
                )
                return

            logger.info(f"Detected {len(detected_items)} items")
            self.progress.emit(f"Detected {len(detected_items)} items", 40)

            # Step 2: Coordinate Transformation (20% of work)
            if self._is_cancelled:
                return

            self.progress.emit("Processing item positions...", 50)
            processed_items = []
            for item in detected_items:
                if self._is_cancelled:
                    return

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

            if not processed_items:
                self.error.emit("Failed to process detected items. Check calibration.")
                return

            self.progress.emit(f"Processed {len(processed_items)} items", 60)

            # Step 3: Database Operations (10% of work)
            if self._is_cancelled:
                return

            self.progress.emit("Saving scan data...", 70)
            desk_bounds = self.calibration.get_desk_bounds_json()
            scan_id = self.db.save_scan(
                self.params['profile_id'],
                self.params['image_path'],
                self.calibration.scale_factor,
                desk_bounds
            )

            self.db.save_detected_items(scan_id, processed_items)
            self.progress.emit("Scan data saved", 75)

            # Step 4: Ergonomic Analysis (25% of work)
            if self._is_cancelled:
                return

            self.progress.emit("Analyzing ergonomics...", 80)
            desk_width_cm, desk_height_cm = self.calibration.get_desk_dimensions_cm()
            analysis = self.ergonomic_engine.analyze_ergonomics(
                scan_id,
                self.params['role'],
                desk_width_cm,
                desk_height_cm,
                self.params['handedness']
            )

            self.progress.emit("Analysis complete!", 95)

            # Step 5: Prepare Results
            if self._is_cancelled:
                return

            results = {
                'scan_id': scan_id,
                'detected_items': detected_items,
                'processed_items': processed_items,
                'analysis': analysis
            }

            self.progress.emit("Finalizing results...", 100)
            logger.info(f"Analysis completed. Score: {analysis['score']}")
            self.finished.emit(results)

        except Exception as e:
            logger.error(f"Analysis worker error: {e}", exc_info=True)
            self.error.emit(f"Analysis failed: {str(e)}")
