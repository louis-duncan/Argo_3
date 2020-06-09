import json
import socket
from threading import Thread
from queue import SimpleQueue


class InvalidUpdateError(Exception):
    pass


class Update:
    def __init__(self, source, seq, target, action, value, **kwargs):
        self.source = source  # Source address.
        self.seq = seq  # Sequential number.
        self.target = target  # The target of the action.
        self.action = action  # Action descriptor.
        self.value = value  # Action value.

    def __repr__(self):
        return f"{self.action} - {self.value}"


class Communicator:
    def __init__(self, server_address):
        self.socket = socket.create_connection(server_address)
        self.connected = True
        self.seq = 0  # The sequential number for the communicator.
        self.updates = SimpleQueue()

        self.receive_thread = Thread(target=self._receive_loop)
        self.receive_thread.start()

    def send_update(self, action, value):
        if not self.connected:
            raise ConnectionAbortedError
        data = {
            "seq": self.seq,
            "action": action,
            "value": value
        }
        data = json.dumps(data).encode() + b"\0"
        self.seq += 1
        try:
            return self.socket.send(data)
        except ConnectionError as e:
            self.socket.close()
            self.connected = False
            raise e

    def _receive_loop(self):
        current_message = b""
        while self.connected:
            try:
                b = self.socket.recv(1)
                # noinspection DuplicatedCode
                if b == b"":
                    self.connected = False
                elif b == b"\0":
                    # Convert current message to an object and purge.
                    data = json.loads(current_message.decode())
                    current_message = b""

                    # Check all required keys exist.
                    if all(k in ("seq", "target", "action", "value") for k in data.keys()):
                        self.updates.put(
                            Update(
                                source=self.socket.getpeername(),
                                **data
                            )
                        )
                    else:
                        raise InvalidUpdateError
                else:
                    current_message += b

            except (ConnectionError, OSError, InvalidUpdateError):
                self.connected = False
