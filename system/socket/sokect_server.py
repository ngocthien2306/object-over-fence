import socketio
from system.utils import get_ipv4_address
class SocketIOServer:
    def __init__(self):
        self.sio = socketio.Server(cors_allowed_origins="*")
        self.app = socketio.WSGIApp(self.sio)

        # Dictionary to store connected clients' sids
        self.connected_clients = {}

        # Define event handlers
        self.sio.on("message", self.handle_message)
        self.sio.on("connect", self.handle_connect)
        self.sio.on("disconnect", self.handle_disconnect)

    def handle_message(self, sid, data):
        print(f"Message from {sid}: {data}")
        self.sio.send(sid, "Server received your message!")

    def handle_connect(self, sid, environ):
        print(f"Client {sid} connected")
        # Store the sid in the dictionary when a client connects
        self.connected_clients[sid] = True

    def handle_disconnect(self, sid):
        print(f"Client {sid} disconnected")
        # Remove the sid from the dictionary when a client disconnects
        if sid in self.connected_clients:
            del self.connected_clients[sid]

    def send_message_to_all_clients(self, msg):
        # Send a message to all connected clients
        for sid in self.connected_clients:
            self.sio.send(sid, msg)

    def run(self):
        import eventlet

        # Run the server
        eventlet.wsgi.server(eventlet.listen((get_ipv4_address(), 5000)), self.app)


if __name__ == "__main__":
    server = SocketIOServer()
    server.run()

    # Send a message to all connected clients
    server.send_message_to_all_clients("Hello, clients!")
