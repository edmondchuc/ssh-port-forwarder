from typing import Callable
from uuid import uuid4

from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from loguru import logger

from ssh_port_forwarder.desktop.input_field import InputField
from ssh_port_forwarder.desktop.label import H1, H2
from ssh_port_forwarder.models import Connection
from ssh_port_forwarder.desktop.connection_service import connection_service


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

        name_input = InputField("Name", "Project A")
        layout.addWidget(name_input)
        self.name_input = name_input

        host_input = InputField("Host", "devbox")
        layout.addWidget(host_input)
        self.host_input = host_input

        description_input = InputField("Description", "...")
        layout.addWidget(description_input)
        self.description_input = description_input

        ports_h2 = H2("Ports")
        layout.addWidget(ports_h2)

        # TODO: Add a delete port button
        self.port_inputs: list[InputField] = []
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

        port_input = InputField("Port", "8080")
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
            port_input = InputField("Port")
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
