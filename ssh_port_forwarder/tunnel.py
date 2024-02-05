import sshtunnel
from loguru import logger

from ssh_port_forwarder.models import Connection


class Tunnel:
    def __init__(self, port: int, connection: Connection):
        super().__init__()
        self.port = port
        self.connection = connection
        self.tunnel = sshtunnel.SSHTunnelForwarder(
            (connection.host, connection.ssh_port),
            remote_bind_address=("localhost", port),
            local_bind_address=("localhost", port),
        )

    def start(self):
        self.tunnel.start()
        logger.debug(
            f"Tunnel is running on localhost:{self.port} - {self.connection.name}"
        )

    def stop(self):
        self.tunnel.stop()
        logger.debug(
            f"Tunnel stopped on localhost:{self.port} - {self.connection.name}"
        )
