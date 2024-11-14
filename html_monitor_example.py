from flask import Flask, render_template
from flask_socketio import SocketIO
import asyncio
import threading

from app_monitor import SocketManager
from app_monitor.server import OrderedDecoder, SerialUpdateServer
from app_monitor.elements_base import TextElement

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

# Initialize SocketManager with Flask-SocketIO instance
manager = SocketManager(socketio=socketio, frequency=20)  # 20Hz update rate

# Define and add elements to the manager
text_element1 = TextElement(element_id="element1")
text_element2 = TextElement(element_id="element2")
text_element3 = TextElement(element_id="element3")
manager.add_element(text_element1)
manager.add_element(text_element2)
manager.add_element(text_element3)

# Set up the Serial Update Server
server = SerialUpdateServer(
    manager,
    port="/dev/tty.usbserial-1460",
    baudrate=115200,
    decoder=OrderedDecoder(keys=["element1", "element2", "element3"]),
)


@app.route("/")
def index():
    return render_template("example.html")


def run_flask():
    """Run Flask in a separate thread."""
    socketio.run(app, port=5000)


async def main():
    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Start the asyncio tasks
    await asyncio.gather(manager.push_data(), server.start(frequency=20))


if __name__ == "__main__":
    asyncio.run(main())
