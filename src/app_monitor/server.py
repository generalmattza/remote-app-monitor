from abc import abstractmethod
import asyncio
import zmq
import zmq.asyncio
import serial

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
    """Class to manage updates via a serial connection asynchronously."""

    def __init__(
        self,
        monitor_manager,
        serial_instance=None,
        port="/dev/ttyUSB0",
        baudrate=9600,
        decoder=None,
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
            self.decoder = decoder

    async def start(self, frequency: float = 30):
        """Start the serial reader asynchronously by polling the serial port."""
        assert frequency > 0, "Frequency must be greater than 0."
        assert self.serial_connection.is_open, "Serial connection is not open."

        try:
            while True:
                # If there is data on the serial port, then read it
                if self.serial_connection.in_waiting:
                    # Read available data on the serial port
                    if data := self.serial_connection.readline():
                        if self.decoder:
                            data = self.decoder.decode(data)
                        self.process_update(data)
                await asyncio.sleep(1 / frequency)

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
        return dict(zip(self.keys, data))
