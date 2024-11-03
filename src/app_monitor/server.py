import asyncio
import io
import zmq
import zmq.asyncio
import serial
import logging

from .logger import logger


class UpdateServer:
    """Class to manage updates synchronously."""

    def __init__(
        self,
        monitor_manager,
        dict_encoding_map=None,
        enable_hex=False,
        fixed_point_scaling=False,
    ):
        self.monitor_manager = monitor_manager
        self.dict_encoding_map = dict_encoding_map
        self.enable_hex = enable_hex
        self.fixed_point_scaling = fixed_point_scaling
        self.scale = 100.0 if self.fixed_point_scaling else 1.0

    def process_update(self, message):
        """Process updates received via message."""
        try:
            for part in filter(None, message.split(",")):
                element_id, *update_args = part.split()
                if self.dict_encoding_map:
                    element_id = self.dict_encoding_map.get(element_id, element_id)
                try:
                    if self.enable_hex:
                        update_args = [int(arg, 16) / self.scale for arg in update_args]
                    else:
                        update_args = [float(arg) / self.scale for arg in update_args]
                except ValueError:
                    pass
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
        self,
        monitor_manager,
        dict_encoding_map=None,
        enable_hex=False,
        serial_instance=None,
        port="/dev/ttyUSB0",
        baudrate=9600,
    ):
        super().__init__(monitor_manager, dict_encoding_map, enable_hex)
        if serial_instance:
            self.serial_connection = serial_instance
            self.port = serial_instance.port
            self.baudrate = serial_instance.baudrate
        else:
            self.serial_connection = serial.Serial(port=port, baudrate=baudrate)
            self.port = port
            self.baudrate = baudrate
        self.running = True
        self.buffer = ""

    async def start_reader(self, interval: float = 0.1):
        """Start the serial reader asynchronously by polling the serial port."""
        try:
            while True:
                if self.serial_connection.in_waiting > 0:
                    # Read available data
                    data = self.serial_connection.read(
                        self.serial_connection.in_waiting
                    ).decode("utf-8")
                    self.buffer += data  # Accumulate data in buffer

                    # Split buffer on commas to get complete values
                    *messages, self.buffer = self.buffer.split(",")

                    # Process each complete message
                    for message in messages:
                        if message:  # Skip empty messages
                            # logger.debug(message.strip())
                            self.process_update(message.strip())

                await asyncio.sleep(interval)

        except Exception as e:
            logger.error(f"Error in serial connection: {e}")
        finally:
            self.serial_connection.close()
            logger.info("Serial connection closed.")

    async def reconnect(self, delay=5):
        """Attempt to reconnect to the serial port after a delay."""
        self.serial_connection.close()
        await asyncio.sleep(delay)  # Wait before attempting to reconnect
        try:
            self.serial_connection.open()
            logger.info(f"Reconnected to serial port {self.port}.")
        except Exception as e:
            logger.error(f"Failed to reconnect: {e}")

    def stop(self):
        """Stop the serial reader loop."""
        self.running = False
