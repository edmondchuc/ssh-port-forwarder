import importlib.metadata
import sys
import logging
from typing import Callable
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QApplication,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QDialog,
    QLineEdit,
    QFrame,
    QHBoxLayout,
    QCheckBox,
    QMessageBox,
)
from PySide6.QtGui import QIcon
from loguru import logger

from ssh_port_forwarder.log_handlers import InterceptHandler
from ssh_port_forwarder.models import Connection
from ssh_port_forwarder.services import connection_service
from ssh_port_forwarder.app_dir import app_dir


class H1(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        font = self.font()
        font.setPointSize(24)
        self.setFont(font)


class H2(QLabel):
    def __init__(self, text: str):
        super().__init__(text)
        font = self.font()
        font.setPointSize(20)
        self.setFont(font)


class Input(QFrame):
    def __init__(self, label: str | None = None, placeholder: str = ""):
        super().__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        if label is not None:
            input_label = QLabel(label)
            layout.addWidget(input_label)

        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        layout.addWidget(input_field)
        self.input_field = input_field


class NewConnectionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("New connection")

        self.button_row = None
        self.forward_a_port_btn = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        h1 = H1("New Connection")
        layout.addWidget(h1)
        self.h1 = h1

        name_input = Input("Name", "Project A")
        layout.addWidget(name_input)
        self.name_input = name_input

        host_input = Input("Host", "devbox")
        layout.addWidget(host_input)
        self.host_input = host_input

        description_input = Input("Description", "...")
        layout.addWidget(description_input)
        self.description_input = description_input

        ports_h2 = H2("Ports")
        layout.addWidget(ports_h2)

        # TODO: Add a delete port button
        self.port_inputs: list[Input] = []
        self.init_create_children()

    def init_create_children(self):
        self.create_add_a_port_btn()
        self.create_button_row()

    def save_btn_callback(self):
        id_ = str(uuid4())
        name = self.name_input.input_field.text()
        host = self.host_input.input_field.text()
        description = self.description_input.input_field.text()

        connection = Connection(
            id=id_,
            name=name,
            host=host,
            description=description if description != "" else None,
            ports=[
                int(port.input_field.text())
                for port in self.port_inputs
                if port.input_field.text() != ""
            ],
        )
        connection_service.create(connection)
        logger.info(f"Created new connection: {connection}")
        self.close()

    def create_button_row(self):
        button_row = QWidget()
        self.layout().addWidget(button_row)
        layout = QHBoxLayout()
        button_row.setLayout(layout)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_btn_callback)
        layout.addWidget(save_btn)
        self.button_row = button_row

    def create_add_a_port_btn(self):
        layout = self.layout()
        self.forward_a_port_btn = QPushButton("Add a port")
        self.forward_a_port_btn.clicked.connect(self.create_port_input_widget)
        layout.addWidget(self.forward_a_port_btn)

    def create_port_input_widget(self):
        layout = self.layout()

        layout.removeWidget(self.forward_a_port_btn)
        self.forward_a_port_btn.deleteLater()
        layout.removeWidget(self.button_row)
        self.button_row.deleteLater()

        port_input = Input("Port", "8080")
        self.port_inputs.append(port_input)
        layout.addWidget(port_input)
        self.create_add_a_port_btn()
        self.create_button_row()


class EditConnectionDialog(NewConnectionDialog):
    def __init__(self, connection: Connection, parent_redraw_function: Callable):
        self.connection = connection
        self.parent_redraw_function = parent_redraw_function
        super().__init__()
        self.setWindowTitle("Edit connection")
        self.h1.setText("Edit connection")
        self.name_input.input_field.setText(connection.name)
        self.host_input.input_field.setText(connection.host)
        self.description_input.input_field.setText(connection.description)

    def init_create_children(self):
        layout = self.layout()
        for port in self.connection.ports:
            port_input = Input("Port")
            port_input.input_field.setText(str(port))
            self.port_inputs.append(port_input)
            layout.addWidget(port_input)
        self.create_add_a_port_btn()
        self.create_button_row()

    def save_btn_callback(self):
        id_ = self.connection.id
        name = self.name_input.input_field.text()
        host = self.host_input.input_field.text()
        description = self.description_input.input_field.text()

        connection = Connection(
            id=id_,
            name=name,
            host=host,
            description=description if description != "" else None,
            ports=[
                int(port.input_field.text())
                for port in self.port_inputs
                if port.input_field.text() != ""
            ],
            enabled=self.connection.enabled,
        )

        try:
            connection_service.edit(connection)
        except Exception as err:
            logger.error(
                f"Error enabling connection {self.connection.id}. Error: {err}"
            )
            connection_service.set_enabled(self.connection.id, False)
            self.parent.parent_redraw_function()

        self.close()


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

        self.draw_connections()

        new_connection_btn = QPushButton("New connection")
        new_connection_btn.clicked.connect(self.create_new_connection_dialog)
        layout.addWidget(new_connection_btn)
        self.new_connection_btn = new_connection_btn

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


if __name__ == "__main__":
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
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
