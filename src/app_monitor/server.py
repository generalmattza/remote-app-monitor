from abc import abstractmethod
import asyncio
import zmq
import zmq.asyncio
import serial
import struct
from collections import OrderedDict
from .logger import logger


class UpdateServer:
    """Class to manage updates synchronously."""

    def __init__(
        self,
        monitor_manager,
    ):
        self.monitor_manager = monitor_manager

    def process_update(self, packet):
        """Process updates received via message."""

        # logger.debug(f"Received packet: {packet}")

        for element_id, value in packet.items():
            try:
                self.monitor_manager.update(element_id, value)
            except Exception as e:
                logger.error(f"Error processing update: {e}")

    @abstractmethod
    def start(self):
        """Start the update server."""
        ...


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

    async def start(self):
        """Start the ZeroMQ subscriber asynchronously."""
        logger.info(f"Subscribed to {self.host}:{self.port}")
        while True:
            message = await self.socket.recv_string()  # Non-blocking receive
            self.process_update(message)


class SerialUpdateServer(UpdateServer):
    """Class to manage updates via a serial or ethernet connection asynchronously."""

    def __init__(
        self,
        monitor_manager,
        detect_devices=False,
        serial_instance=None,
        port="/dev/ttyUSB0",
        baudrate=9600,
        decoder=None,
        validator=None,
    ):
        super().__init__(monitor_manager)
        if serial_instance:
            self.connection = serial_instance
        elif detect_devices:
            self.connection = self.detect_devices(baudrate=baudrate)
        else:
            self.connection = serial.Serial(port=port, baudrate=baudrate)

        self.decoder = decoder
        self.validator = validator

    def detect_devices(
        self,
        search: str = r"usb",
        pattern: str = "/dev/tty*",
        baudrate=9600,
    ):

        def find_devices(search, pattern):
            import glob
            import re

            # List all files matching the pattern /dev/tty*
            files = glob.glob(pattern)

            # Filter files that contain 'usb'
            devices = [f for f in files if re.search(search, f)]

            return devices

        if devices := find_devices(search, pattern):
            for device in devices:
                try:
                    serial_device = serial.Serial(port=device, baudrate=baudrate)
                    return serial_device
                except Exception as e:
                    logger.error(f"Error connecting to {device}: {e}")

    async def start(self, frequency: float = 30):
        """Start the reader asynchronously by polling the connection."""
        if frequency <= 0:
            raise ValueError("Frequency must be greater than 0.")
        if not self.connection.is_open:
            raise RuntimeError("Connection is not open.")

        try:
            while True:
                if self.connection.in_waiting:
                    if data := self.connection.readline():
                        if self.validator:
                            data = self.validator.validate(data)
                        if self.decoder and data:
                            data = self.decoder.decode(data)
                        if data:
                            self.process_update(data)
                await asyncio.sleep(1 / frequency)

        except Exception as e:
            logger.error(f"Error in connection: {e}")
        finally:
            if hasattr(self.connection, 'stop'):
                self.connection.stop()
            elif hasattr(self.connection, 'close'):
                self.connection.close()
            logger.info("Connection closed.")


class Decoder:
    @abstractmethod
    def decode(self, packet): ...


class OrderedDecoder(Decoder):
    """Class to decode packets based on ordered keys."""

    def __init__(self, keys, separator=","):
        self.keys = keys
        self.separator = separator

    def decode(self, packet):
        data = packet.decode("utf-8").strip().split(self.separator)
        return OrderedDict(zip(self.keys, data))


class StructDecoder(Decoder):
    def __init__(self, data_keys, packet_format=None):
        self.packet_format = packet_format
        self.data_keys = data_keys

    def decode(self, packet):
        if self.packet_format:
            packet = struct.unpack(self.packet_format, packet)
        if self.data_keys:
            packet = OrderedDict(zip(self.data_keys, packet))
        return packet


class Validator:
    @abstractmethod
    def validate(self, packet): ...


class WindowValidator(Validator):
    def __init__(self, window_size=10, start_byte=0xA5, end_byte=0x5A):
        self.window_size = window_size
        self.start_byte = start_byte
        self.end_byte = end_byte

    def validate(self, packet):
        if (
            len(packet) == self.window_size
            and packet[0] == self.start_byte
            and packet[-1] == self.end_byte
        ):
            # Return packet without start and end bytes
            return packet[1:-1]
        return False
