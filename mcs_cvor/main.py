"""Main entry point for MCS CVOR Remote Management System."""
import os
import sys

# Add repo root to sys.path so `python mcs_cvor/main.py` works from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from PyQt6.QtWidgets import QApplication
    from mcs_cvor.database.db_manager import DBManager
    from mcs_cvor.ui.main_window import MainWindow
    from mcs_cvor.utils.logger import get_logger

    logger = get_logger("mcs_cvor")
    logger.info("Starting MCS CVOR Remote Management System")

    app = QApplication(sys.argv)
    app.setApplicationName("MCS CVOR")
    app.setOrganizationName("SAAF")
    app.setStyle("Fusion")

    db = DBManager()
    window = MainWindow(db)
    window.show()
    logger.info("Main window displayed")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
