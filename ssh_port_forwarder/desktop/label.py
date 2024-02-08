from PySide6.QtWidgets import QLabel


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
