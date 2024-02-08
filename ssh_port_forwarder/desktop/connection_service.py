from collections import defaultdict

from tinydb import TinyDB, Query
from loguru import logger

from ssh_port_forwarder.db import db
from ssh_port_forwarder.models import Connection
from ssh_port_forwarder.tunnel import Tunnel

query = Query()


# TODO: Currently used as a singleton to also keep track of tunnel objects.
class ConnectionService:
    def __init__(self, db: TinyDB):
        super().__init__()
        self.db = db

        # A dict containing connection id and dict of port and tunnel object key-value pair.
        self.tunnels: dict[str, dict[int, Tunnel]] = defaultdict(dict)

    def init(self):
        connections = self.get_all()

        # Create tunnel objects and start them if they are enabled.
        for connection in connections:
            for port in connection.ports:
                if connection.enabled:
                    tunnel = Tunnel(port, connection)
                    self.tunnels[connection.id][port] = tunnel
                    if connection.enabled:
                        try:
                            tunnel.start()
                        except Exception as err:
                            logger.error(
                                f"Failed starting tunnel for {connection} on port {port}. Error: {err}"
                            )
                            self.set_enabled(connection.id, False)

    def shutdown(self):
        for connection_id in self.tunnels:
            for port in self.tunnels[connection_id]:
                tunnel = self.tunnels[connection_id][port]
                if tunnel.tunnel.is_active:
                    tunnel.stop()

    def create(self, connection: Connection) -> int:
        doc = self.db.insert(connection.model_dump())
        self._recreate_and_start_tunnels(connection)
        return doc

    def get(self, id_: str) -> Connection:
        doc = self.db.get(query.id == id_)
        if doc is not None:
            return Connection(**doc)
        raise RuntimeError(f"Connection with id {id_} not found")

    def get_all(self) -> list[Connection]:
        return [Connection(**item) for item in self.db.all()]

    def set_enabled(self, id_: str, enabled: bool) -> None:
        doc_ids = self.db.update({"enabled": enabled}, query.id == id_)
        for doc_id in doc_ids:
            connection = Connection(**self.db.get(doc_id=doc_id))
            ports = self.tunnels[connection.id].keys()
            if enabled:
                self._recreate_and_start_tunnels(connection)
            else:
                for port in ports:
                    logger.info(f"Disabled {port} - {connection.name}")
                    self.tunnels[connection.id][port].stop()

    def edit(self, connection: Connection) -> int | None:
        updated_docs = self.db.update(
            connection.model_dump(), query.id == connection.id
        )
        if updated_docs:
            logger.info(f"Updated connection: {connection}")
            if connection.enabled:
                self._recreate_and_start_tunnels(connection)

            return updated_docs[0]

    def _recreate_and_start_tunnels(self, connection: Connection):
        # Stop all tunnels for this connection.
        for tunnel in self.tunnels[connection.id].values():
            if tunnel.tunnel.is_active:
                tunnel.stop()

        # For each port in connection, create a new tunnel and start it.
        for port in connection.ports:
            if connection.enabled:
                tunnel = Tunnel(port, connection)
                self.tunnels[connection.id][port] = tunnel
                if connection.enabled:
                    tunnel.start()

        logger.info(f"Recreated and started all tunnels - {connection.name}")


connection_service = ConnectionService(db)
