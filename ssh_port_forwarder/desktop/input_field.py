from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QLineEdit


class InputField(QFrame):
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
