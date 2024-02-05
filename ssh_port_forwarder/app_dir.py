from pathlib import Path

from PySide6.QtCore import QStandardPaths

user_specific_data_location = QStandardPaths.writableLocation(
    QStandardPaths.AppDataLocation
)
app_dir_name = "com.edmondchuc.SSHPortForwarder"
app_dir = Path(user_specific_data_location) / app_dir_name
app_dir.mkdir(exist_ok=True)
