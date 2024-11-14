from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import serial
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)


# Route to serve the HTML page
@app.route("/")
def index():
    return render_template("index.html")


# Background thread to read from serial and emit data over WebSocket
def read_serial_data():
    with serial.Serial(
        "/dev/tty.usbserial-1440", 115200
    ) as ser:  # Update serial port as needed
        while True:
            data = ser.readline().decode().strip()  # Read data from serial
            socketio.emit(
                "serial_data", {"data": data}
            )  # Send data to WebSocket clients
            time.sleep(0.05)  # Adjust for desired refresh rate (e.g., 0.1 for 10Hz)


# Start the Flask-SocketIO server and the serial data reading thread
if __name__ == "__main__":
    # Start the serial reading in a background thread
    serial_thread = threading.Thread(target=read_serial_data)
    serial_thread.daemon = True  # Daemonize thread to exit with the main program
    serial_thread.start()

    # Run the Flask app with SocketIO
    socketio.run(app, port=5000)
