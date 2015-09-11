import socket
import struct
import queue
import threading
import pickle
import os
from . import puz
from . import model as _model
from . import metrics as _metrics
from .constants import *


# Socket utility
def send(sock: socket.socket, message: bytes):
    """Pack the message length and content for sending larger messages."""
    message = struct.pack('>I', len(message)) + message
    sock.sendall(message)


def recv(sock: socket.socket) -> bytes:
    """Read message length and receive the corresponding amount of data."""
    size = _recv(sock, 4)
    size = struct.unpack('>I', size)[0]
    return _recv(sock, size)


def _recv(sock: socket.socket, size: int) -> bytes:
    """Secondary function to receive a specified amount of data."""
    message = b''
    while len(message) < size:
        packet = sock.recv(size - len(message))
        if not packet:
            sock.close()
            raise OSError("Nothing else to read from socket")
        message += packet
    return message


# Socket wrapper classes
class SocketHandler:

    def __init__(self, sock, address, server):
        self.sock = sock
        self.address = address
        self.server = server
        self.alive = False

        self._receive = threading.Thread(target=self.receive, daemon=True)

    def receive(self):
        while self.alive:
            try:
                event, data = pickle.loads(recv(self.sock))
                self.server.queue.put((event, data, self))
            except Exception as e:
                print("handler receive", e)
                self.stop()

    def emit(self, event: str, data: object):
        send(self.sock, pickle.dumps((event, data)))

    def start(self):
        self.alive = True
        self._receive.start()

    def stop(self):
        self.alive = False
        if self in self.server.handlers:
            self.server.handlers.remove(self)
        self.server.emit(CLIENT_EXITED, "")


class SocketServer:

    handler = SocketHandler

    def __init__(self, address):
        self.address = address
        self.alive = False

        self.queue = queue.Queue()
        self.handlers = []
        self.bindings = {}

        self.sock = socket.socket()
        self.sock.bind(self.address)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.listen(8)

        self.bind("echo", self.echo)

        self._accept = threading.Thread(target=self.accept, daemon=True)

    def accept(self):
        while self.alive:
            try:
                sock, address = self.sock.accept()
                handler = self.handler(sock, address, self)
                handler.start()
                self.handlers.append(handler)
            except Exception as e:
                print("server accept", e)
                self.stop()

    def receive(self):
        while self.alive:
            try:
                event, data, handler = self.queue.get()
                function = self.bindings.get(event)
                if function is None:
                    print("caught event %s with no binding" % event)
                else:
                    function(data, handler)
            except Exception as e:
                print("server serve", e)
                self.stop()

    def emit(self, event: str, data: object, *handlers: SocketHandler):
        handlers = handlers or self.handlers
        for handler in handlers:
            handler.emit(event, data)

    def bind(self, event, function):
        self.bindings[event] = function

    def echo(self, data, handler):
        handler.emit("echo", data)

    def start(self):
        self.alive = True
        self._accept.start()
        self.receive()

    def stop(self):
        self.alive = False
        for handler in self.handlers:
            handler.stop()


class SocketConnection:

    def __init__(self, address):
        self.address = address
        self.alive = False

        self.q = queue.Queue()

        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.connect(self.address)

        self._receive = threading.Thread(target=self.receive, daemon=True)

    def receive(self):
        while self.alive:
            try:
                event, data = pickle.loads(recv(self.sock))
                self.q.put((event, data))
            except Exception as e:
                print("connection receive", e)
                self.stop()

    def emit(self, event: str, data: object):
        send(self.sock, pickle.dumps((event, data)))

    def queue(self, q: queue.Queue):
        self.q = q

    def start(self):
        self.alive = True
        self._receive.start()

    def stop(self):
        self.alive = False


class CrosswordHandler(SocketHandler):

    def __init__(self, sock, address, server):
        super().__init__(sock, address, server)
        self.model = _model.PlayerModel("", "")
        self.id = id(self)


class CrosswordServer(SocketServer):

    handler = CrosswordHandler

    def __init__(self, address):
        super().__init__(address)
        self.model = None
        self.metrics = None

        if not os.path.isdir("puzzles"):
            os.makedirs("puzzles")

        self.bind(PUZZLE_LOADED, self.on_puzzle_loaded)
        self.bind(CLIENT_JOINED, self.on_client_joined)

    def on_puzzle_loaded(self, puzzle: bytes, handler):
        path = os.path.join("puzzles", str(hash(puzzle)) + ".puz")
        with open(path, "w") as file:
            file.write(puzzle)
        self.model = _model.PuzzleModel(puz.read(path))
        self.metrics = _metrics.PuzzleMetrics(self.model)

    def on_client_joined(self, data: dict, handler: CrosswordHandler):
        handler.model.name = data["name"]
        handler.model.color = data["color"]
        data["id"] = handler.id
        handler.emit(ID_ASSIGNED, handler.id)
        self.emit(CLIENT_JOINED, data)
        print("client named '%s' joined" % handler.model.name)


class CrosswordConnection(SocketConnection):

    def __init__(self, address):
        super().__init__(address)


