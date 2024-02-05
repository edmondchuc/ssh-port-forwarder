from tinydb import TinyDB
from loguru import logger

from ssh_port_forwarder.app_dir import app_dir

db_path = app_dir / "data.json"
logger.info(f"Database path: {db_path}")
db = TinyDB(db_path)
