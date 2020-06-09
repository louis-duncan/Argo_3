import socket
import time
from threading import Thread
import json
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


class Client:
    def __init__(self, sock: socket.socket):
        self.open = True
        self.close_state = None
        self.socket = sock
        self.peername = self.socket.getpeername()
        self.updates = SimpleQueue()

        self.receive_thread = Thread(target=self._receive_loop)
        self.receive_thread.start()

    def getpeername(self):
        return self.peername

    def close(self, state="Closed."):
        self.open = False
        return self.socket.close()

    def _receive_loop(self):
        current_message = b""
        while self.open:
            try:
                b = self.socket.recv(1)
                if b == b"":
                    self.close("Client Closed Connection.")
                else:
                    # noinspection DuplicatedCode
                    if b == b"\0":
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
                        current_message += b  # Byte is not EOF and is not a terminator, so add to message.

            except (InvalidUpdateError, json.JSONDecodeError, ConnectionAbortedError, ConnectionError) as e:
                self.open = False
                if type(e) is InvalidUpdateError:
                    msg = "Client sent invalid update data."
                elif type(e) is json.JSONDecodeError:
                    msg = "Client sent invalid JSON data."
                elif type(e) is ConnectionAbortedError:
                    msg = "Socket closed by server."
                else:
                    msg = f"Connection Error. {e}."
                self.close(msg)
                print(f"Client {self.getpeername()} closed.")

    def send_update(self, update: Update):
        if self.socket.getpeername() == update.source:
            return 0
        else:
            data = dict(update.__dict__)
            data.pop("source")
            data = json.dumps(data).encode() + b"\0"
            print(f"Sending update {update} from {update.source} to {self.getpeername()}")
            return self.socket.send(data)


class Server:
    def __init__(self, address="0.0.0.0", port=8989, game=None):
        self.game = game
        self.run = True
        self.clients = []

        self.updates = SimpleQueue()
        self.to_send = SimpleQueue()

        # Set up server socket.
        self.socket = socket.socket()
        self.socket.bind((address, port))
        self.socket.listen(5)

        # Start threads.
        self.connection_thread = Thread(target=self._connect_loop)
        self.connection_thread.start()

        self.receive_thread = Thread(target=self._receive_loop)
        self.receive_thread.start()

        self.send_thread = Thread(target=self._send_loop)
        self.send_thread.start()

        self.event_handler_thread = Thread(target=self._process_updates)
        self.event_handler_thread.start()

    def _connect_loop(self):
        while self.run:
            new, addr = self.socket.accept()
            to_go = []
            for client in self.clients:
                if client.open:
                    try:
                        if client.getpeername() == addr:
                            to_go.append(client)
                    except OSError:
                        to_go.append(client)
                else:
                    to_go.append(client)
            for cs in to_go:
                self.clients.remove(cs)
            self.clients.append(Client(new))
            print(f"New client connected from {new.getpeername()}.")

    def _receive_loop(self):
        while self.run:
            client: Client
            for client in self.clients:
                for i in range(client.updates.qsize()):
                    self.updates.put(client.updates.get())
            time.sleep(0.1)

    def _send_loop(self):
        while self.run:
            while not self.to_send.empty():
                u: Update = self.to_send.get()
                for client in self.clients:
                    if u.source != client.getpeername():
                        client.send_update(u)
                time.sleep(0.1)
            time.sleep(0.1)

    def _process_updates(self):
        while self.run:
            while not self.updates.empty():
                u: Update = self.updates.get()
                if self.game is not None:
                    self.game.pass_action(
                        u.target,
                        u.action,
                        u.value
                    )
                self.to_send.put(u)
                time.sleep(0.1)
            time.sleep(0.1)


class Game:
    def pass_action(self, target, action, value):
        pass