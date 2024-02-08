import threading

from PySide6.QtCore import Qt, QObject, Signal, Slot
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from loguru import logger

from ssh_port_forwarder.desktop.connection_dialog import NewConnectionDialog
from ssh_port_forwarder.desktop.connection_item import ConnectionItem
from ssh_port_forwarder.desktop.label import H1
from ssh_port_forwarder.desktop.connection_service import connection_service


class StartupWorker(QObject):
    completed = Signal()

    def __init__(self):
        super().__init__()

    @Slot()
    def init(self):
        connection_service.init()
        self.completed.emit()


class MainWindow(QMainWindow):
    def __init__(self, version):
        super().__init__()
        self.setWindowTitle(f"v{version}")

        # TODO: Only apply this if OS is macOS.
        self.setUnifiedTitleAndToolBarOnMac(True)

        self.connections: list[ConnectionItem] = []

        layout = QVBoxLayout()
        layout_widget = QWidget()
        layout_widget.setLayout(layout)
        self.setCentralWidget(layout_widget)

        h1 = H1("Connections")
        layout.addWidget(h1)
        h1.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.loading_label = QLabel("Loading...")
        layout.addWidget(self.loading_label)

        self.worker = StartupWorker()
        self.worker_thread = threading.Thread(target=self.worker.init)
        self.worker.completed.connect(self.init_callback)
        self.worker_thread.start()

    def draw(self):
        self.draw_connections()
        self.draw_new_connection_button()

    def draw_new_connection_button(self):
        layout = self.centralWidget().layout()
        new_connection_btn = QPushButton("New connection")
        new_connection_btn.clicked.connect(self.create_new_connection_dialog)
        layout.addWidget(new_connection_btn)
        self.new_connection_btn = new_connection_btn

    def init_callback(self):
        layout = self.centralWidget().layout()
        layout.removeWidget(self.loading_label)
        self.loading_label.deleteLater()
        self.draw()

    def draw_connections(self):
        layout = self.centralWidget().layout()
        connections = connection_service.get_all()
        self.connections = [
            ConnectionItem(connection, self.redraw_connections)
            for connection in connections
        ]
        for connection in self.connections:
            layout.addWidget(connection)

    def redraw_connections(self):
        layout = self.centralWidget().layout()
        layout.removeWidget(self.new_connection_btn)
        for connection_item in self.connections:
            layout.removeWidget(connection_item)
            connection_item.deleteLater()
        self.draw_connections()
        layout.addWidget(self.new_connection_btn)

    def create_new_connection_dialog(self):
        dialog = NewConnectionDialog()
        dialog.exec()
        self.redraw_connections()

    def closeEvent(self, event):
        connection_service.shutdown()
        logger.info("Shutting down")
