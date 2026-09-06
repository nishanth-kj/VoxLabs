import sys
import os
# Add the api root to sys.path so backend imports work correctly
api_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_root not in sys.path:
    sys.path.insert(0, api_root)

from PyQt6.QtWidgets import QApplication
from desktop.components.main_window import MainWindow
from utils.logger import logger

def main():
    logger.info("Starting VoxLabs Desktop Application...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    logger.info("VoxLabs Desktop UI initialized and running.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
