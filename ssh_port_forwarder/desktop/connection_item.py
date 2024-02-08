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

    def __init__(self):
        super().__init__()

    @Slot()
    def work(self):
        ...


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

        enabled = QCheckBox("Enabled")
        enabled.setChecked(connection.enabled)
        enabled.stateChanged.connect(self.enabled_callback)
        layout.addWidget(enabled)
        self.enabled = enabled

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.create_edit_dialog)
        layout.addWidget(edit_btn)

    def create_edit_dialog(self):
        self.connection = connection_service.get(self.connection.id)
        dialog = EditConnectionDialog(self.connection, self.parent_redraw_function)
        dialog.exec()

    def enabled_callback(self, state):
        if state == Qt.CheckState.Checked.value:
            logger.info(
                f"Enabling connection {self.connection.id} - {self.connection.name}"
            )
            try:
                connection_service.set_enabled(self.connection.id, True)
            except Exception as err:
                logger.error(
                    f"Error enabling connection {self.connection.id}. Error: {err}"
                )
                connection_service.set_enabled(self.connection.id, False)
                self.parent_redraw_function()
                msg_box = QMessageBox()
                msg_box.setWindowTitle("Error")
                msg_box.setText(str(err))
                msg_box.exec()
        else:
            logger.info(
                f"Disabling connection {self.connection.id} - {self.connection.name}"
            )
            connection_service.set_enabled(self.connection.id, False)
