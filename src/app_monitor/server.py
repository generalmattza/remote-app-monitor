import asyncio
import zmq
import zmq.asyncio
import serial
import logging

from .logger import logger


class UpdateServer:
    """Class to manage updates synchronously."""

    def __init__(self, monitor_manager):
        self.monitor_manager = monitor_manager

    def process_update(self, message):
        """Process updates received via message."""
        try:
            # Assuming message is in the format: "element_id var header value"
            parts = message.split(",")
            for part in parts:
                update_info = part.split()
                element_id = update_info[0]
                update_args = update_info[1:]
                self.monitor_manager.update(element_id, *update_args)
        except Exception as e:
            logger.error(f"Error processing update: {e}")


class ZeroMQUpdateServer(UpdateServer):
    """Class to manage updates via ZeroMQ PUB-SUB pattern asynchronously."""

    def __init__(self, monitor_manager, host="localhost", port=5556):
        super().__init__(monitor_manager)
        self.host = host
        self.port = port
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)  # Subscriber socket
        self.socket.connect(f"tcp://{self.host}:{self.port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

    async def start_subscriber(self):
        """Start the ZeroMQ subscriber asynchronously."""
        logger.info(f"Subscribed to {self.host}:{self.port}")
        while True:
            message = await self.socket.recv_string()  # Non-blocking receive
            self.process_update(message)


class SerialUpdateServer(UpdateServer):
    """Class to manage updates via a serial connection asynchronously."""

    def __init__(
        self, monitor_manager, serial_instance=None, port="/dev/ttyUSB0", baudrate=9600
    ):
        super().__init__(monitor_manager)
        if serial_instance:
            self.serial_connection = serial_instance
            self.port = serial_instance.port
            self.baudrate = serial_instance.baudrate
        else:
            self.serial_connection = serial.Serial(port=port, baudrate=baudrate)
            self.port = port
            self.baudrate = baudrate

    async def start_reader(self):
        """Start the serial reader asynchronously by polling the serial port."""
        try:
            logger.info(
                f"Connecting to serial port {self.port} at {self.baudrate} baud."
            )
            while True:
                if self.serial_connection.in_waiting > 0:
                    message = self.serial_connection.readline().decode("utf-8").strip()
                    self.process_update(message)
                await asyncio.sleep(
                    0.1
                )  # Poll every 100ms to avoid blocking the event loop

        except Exception as e:
            logger.error(f"Error in serial connection: {e}")
        finally:
            self.serial_connection.close()
