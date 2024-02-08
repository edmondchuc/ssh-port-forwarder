import importlib.metadata
import sys
import logging

from PySide6.QtWidgets import (
    QApplication,
)
from PySide6.QtGui import QIcon
from loguru import logger

from ssh_port_forwarder.desktop.main_window import MainWindow
from ssh_port_forwarder.log_handlers import InterceptHandler
from ssh_port_forwarder.app_dir import app_dir

if __name__ == "__main__":
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.ERROR, force=True)
    logger.add(app_dir / "logs/log_{time}.log", rotation="500 MB")

    # TODO: We are missing the logging when connection service is created.
    version = importlib.metadata.version("ssh-port-forwarder")
    logger.info(f"Starting up SSH Port Forwarder v{version}")

    app = QApplication(sys.argv)
    app.setApplicationName("SSH Port Forwarder")
    app.setApplicationVersion(version)

    icon = QIcon("img/icon.jpeg")
    app.setWindowIcon(icon)

    window = MainWindow(version)
    window.show()
    sys.exit(app.exec())
