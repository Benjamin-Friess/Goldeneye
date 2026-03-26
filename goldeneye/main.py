"""Application entry point."""

import sys

from PyQt6.QtWidgets import QApplication

from goldeneye.core.config import settings
from goldeneye.core.logging import setup_logging
from goldeneye.views.main_window import MainWindow


def main() -> None:
    setup_logging(settings.log_level)

    app = QApplication(sys.argv)
    app.setApplicationName("Goldeneye")
    app.setOrganizationName("Benjamin-Friess")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
