import zmq
import zmq.asyncio


class UpdateManager:
    """Class to manage updates from different sources."""

    def __init__(self, monitor_manager):
        self.monitor_manager = monitor_manager

    def process_update(self, message):
        """Process updates received from different sources."""
        try:
            # Assuming message is in the format: "element_id var header value"
            update_info = message.split()
            element_id = update_info[0]
            update_args = update_info[1:]
            self.monitor_manager.update(element_id, *update_args)
        except Exception as e:
            print(f"Error processing update: {e}")


class ZeroMQUpdateManager(UpdateManager):
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
        print(f"Subscribed to {self.host}:{self.port}")
        while True:
            message = await self.socket.recv_string()  # Non-blocking receive
            self.process_update(message)


class SerialUpdateManager(UpdateManager):
    """Class to manage updates via serial communication."""

    def __init__(self, monitor_manager, serial_port):
        super().__init__(monitor_manager)
        self.serial_port = serial_port

    async def start_serial_listener(self):
        """Start the serial listener asynchronously."""
        while True:
            message = await self.read_serial_data()
            self.process_update(message)

    async def read_serial_data(self):
        """Read data from the serial port."""
        # Assume this function reads data asynchronously from the serial port
        return "element_id var header value"
