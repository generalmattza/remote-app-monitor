from flask import Flask, render_template
from flask_socketio import SocketIO
import asyncio
import threading

from app_monitor import SocketManager
from app_monitor.server import OrderedDecoder, SerialUpdateServer
from app_monitor.elements_base import TextElement
from app_monitor.text_formatter import TextFormat

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

# Initialize SocketManager with Flask-SocketIO instance
manager = SocketManager(socketio=socketio, frequency=20)  # 20Hz update rate

text_format = TextFormat(width=9, precision=3, force_sign=True)

data_formats = {
    "position_x": text_format,
    "position_y": text_format,
    "position_z": text_format,
    "motor1_speed": None,
    "motor1_torque": None,
    "motor1_status": None,
    "motor2_speed": None,
    "motor2_torque": None,
    "motor2_status": None,
    "motor3_speed": None,
    "motor3_torque": None,
    "motor3_status": None,
    "motor4_speed": None,
    "motor4_torque": None,
    "motor4_status": None,
}
# Define and add elements to the manager
for name, format in data_formats.items():
    text_element = TextElement(element_id=name, text_format=format)
    manager.add_element(text_element)

# Set up the Serial Update Server
server = SerialUpdateServer(
    manager,
    detect_devices=True,
    baudrate=115200,
    decoder=OrderedDecoder(keys=data_formats.keys()),
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
