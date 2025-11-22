import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from gui.main_window import DeskOptMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DeskOptMainWindow()
    window.show()
    print("DeskOpt application started successfully!")
    print("GUI is running - close the window to exit.")
    sys.exit(app.exec())