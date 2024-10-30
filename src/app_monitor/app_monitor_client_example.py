import zmq
import time
import math
import serial


def gen_sine(amplitude=1, frequency=1, offset=0, phase=0, decimals=2):
    """Generate sine wave values continuously."""
    while True:
        yield round(
            amplitude * math.sin(2 * math.pi * frequency * time.time() + phase)
            + offset,
            decimals,
        )


class ZMQClient:
    """Client class to send data over a ZeroMQ PUB socket."""

    def __init__(self, host="localhost", port=5556):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://{host}:{port}")

    def run(self):
        """Send generated data over the ZeroMQ socket."""
        progress = gen_sine(amplitude=50, frequency=0.1, offset=50)
        processed = iter(range(10000))

        try:
            while True:
                var = next(progress)
                self.socket.send_string(f"temp_range {var}")
                print(f"temp_range={var}")

                processed_val = next(processed)
                self.socket.send_string(f"table_1 Processed 1m {processed_val}")

                time.sleep(1 / 120)
        except KeyboardInterrupt:
            print("ZMQ Client stopped.")
        finally:
            self.socket.close()
            self.context.term()


class SerialClient:
    """Client class to send data over a serial connection."""

    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        self.serial_connection = serial.Serial(port=port, baudrate=baudrate)

    def run(self):
        """Send generated data over the serial connection."""
        progress = gen_sine(amplitude=50, frequency=0.1, offset=50)
        processed = iter(range(1000))

        try:
            while True:
                var = next(progress)
                self.serial_connection.write(f"progress_1 {var}\n".encode("utf-8"))
                print(f"progress_1={var}")

                processed_val = next(processed)
                self.serial_connection.write(
                    f"table_1 Processed 1m {processed_val}\n".encode("utf-8")
                )

                time.sleep(1 / 120)
        except KeyboardInterrupt:
            print("Serial Client stopped.")
        finally:
            self.serial_connection.close()


if __name__ == "__main__":
    # # Create and run the ZeroMQ client
    zmq_client = ZMQClient()
    zmq_client.run()

    # Create and run the Serial client
    # serial_client = SerialClient()
    # serial_client.run()
