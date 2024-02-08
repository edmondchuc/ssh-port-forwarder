import threading
from typing import Callable

from PySide6.QtCore import Qt, QObject, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QMessageBox,
)
from loguru import logger

from ssh_port_forwarder.desktop.connection_dialog import EditConnectionDialog
from ssh_port_forwarder.models import Connection
from ssh_port_forwarder.desktop.connection_service import connection_service


class ConnectionItemWorker(QObject):
    completed = Signal()
    errored = Signal(str)

    def __init__(self):
        super().__init__()

    @Slot()
    def work(self, id_: str, enabled: bool):
        try:
            connection_service.set_enabled(id_, enabled)
            self.completed.emit()
        except Exception as err:
            logger.error(
                f"Error enabling connection {id_}. Error: {err}"
            )
            connection_service.set_enabled(id_, False)
            self.errored.emit(str(err))


class ConnectionItem(QFrame):
    def __init__(self, connection: Connection, parent_redraw_function: Callable):
        self.parent_redraw_function = parent_redraw_function
        super().__init__()
        self.connection = connection
        layout = QVBoxLayout()
        self.setLayout(layout)

        name = QLabel(connection.name)
        layout.addWidget(name)
        self.name = name

        self.enabled_checkbox: QCheckBox | None = None
        self.create_checkbox()

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.create_edit_dialog)
        layout.addWidget(edit_btn)

    def create_checkbox(self):
        layout = self.layout()
        enabled_checkbox = QCheckBox("Enabled")
        enabled_checkbox.setChecked(self.connection.enabled)
        enabled_checkbox.stateChanged.connect(self.enabled_callback)
        layout.addWidget(enabled_checkbox)
        self.enabled_checkbox = enabled_checkbox

    def create_edit_dialog(self):
        self.connection = connection_service.get(self.connection.id)
        dialog = EditConnectionDialog(self.connection, self.parent_redraw_function)
        dialog.exec()

    @Slot(str)
    def display_error(self, err: str):
        self.parent_redraw_function()
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Error")
        msg_box.setText(str(err))
        self.enabled_checkbox.setEnabled(True)
        msg_box.exec()

    def enabled_callback(self, state):
        if state == Qt.CheckState.Checked.value:
            logger.info(
                f"Enabling connection {self.connection.id} - {self.connection.name}"
            )
            self.enabled_checkbox.setDisabled(True)
            worker = ConnectionItemWorker()
            worker_thread = threading.Thread(target=worker.work, args=(self.connection.id, True))
            worker.completed.connect(lambda: self.enabled_checkbox.setEnabled(True))
            worker.errored.connect(self.display_error)
            worker_thread.start()
        else:
            logger.info(
                f"Disabling connection {self.connection.id} - {self.connection.name}"
            )
            self.enabled_checkbox.setDisabled(True)
            worker = ConnectionItemWorker()
            worker_thread = threading.Thread(target=worker.work, args=(self.connection.id, False))
            worker.completed.connect(lambda: self.enabled_checkbox.setEnabled(True))
            worker_thread.start()
