import threading
import socketio
from system.utils import get_ipv4_address
import eventlet

class SocketIOServer:
    def __init__(self, logic_handlers = {}):
        self.sio = socketio.Server(cors_allowed_origins="*")
        self.app = socketio.WSGIApp(self.sio)

        self.connected_clients = {}
        self.logic_handlers = logic_handlers
        self.sio.on("message", self.handle_message)
        self.sio.on("connect", self.handle_connect)
        self.sio.on("disconnect", self.handle_disconnect)

    def handle_message(self, sid, data):
        print(f"Message from {sid}: {data}")
        self.logic_handlers[data['camera_id']].is_start_record = True
        self.sio.send(sid, "Server received your message!")

    def handle_connect(self, sid, environ):
        print(f"Client {sid} connected")
        self.connected_clients[sid] = True

    def handle_disconnect(self, sid):
        print(f"Client {sid} disconnected")
        if sid in self.connected_clients:
            del self.connected_clients[sid]

    def send_message_to_all_clients(self, msg):
        for sid in self.connected_clients:
            self.sio.send(sid, msg)

    def run(self):

        eventlet.wsgi.server(eventlet.listen((get_ipv4_address(), 5000)), self.app)


