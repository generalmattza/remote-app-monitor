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
        element_id_packet_keys=None,
    ):
        self.monitor_manager = monitor_manager
        self.element_id_packet_keys = element_id_packet_keys

    def process_update(self, packet):
        """Process updates received via message."""

        packet_dict = assign_keys_to_packet(packet, self.element_id_packet_keys)

        for element_id, value in packet_dict.items():
            try:
                self.monitor_manager.update(element_id, value)
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
        serial_instance=None,
        port="/dev/ttyUSB0",
        baudrate=9600,
        packet_format='<iiiii',
        element_id_packet_keys=None,
    ):
        super().__init__(monitor_manager, element_id_packet_keys=element_id_packet_keys)
        if serial_instance:
            self.serial_connection = serial_instance
            self.port = serial_instance.port
            self.baudrate = serial_instance.baudrate
        else:
            self.serial_connection = serial.Serial(port=port, baudrate=baudrate)
            self.port = port
            self.baudrate = baudrate
        self.running = True
        self.buffer = b""

        self.packet_format = packet_format
        self.packet_size = struct.calcsize(packet_format)

    async def start_reader(self, interval: float = 0.1):
        """Start the serial reader asynchronously by polling the serial port."""
        try:
            while True:
                # If there is data on the serial port, then read it
                if self.serial_connection.in_waiting:
                    # Read available data on the serial port
                    data = self.serial_connection.read_input()

                    # Accumulate data in buffer
                    if data:
                        self.buffer += data  
                    if self.buffer:
                        # read the freshest packet only from the buffer
                        packet = read_freshest_packet(self.buffer)
                        # process the update
                        self.process_update(packet)
                        # reset buffer, discarding all other data
                        self.buffer = b""
                    
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

import struct


def assign_keys_to_packet(packet, keys):

    # Use zip to pair keys and values, then create a dictionary
    packet_dict = dict(zip(keys, packet))
    
    return packet_dict

import struct

def read_freshest_packet(buffer, packet_size, packet_format):
    # Find the last occurrence of a valid packet in the buffer
    start_index = buffer.rfind(b'\xff')
    
    # Check if there's enough room in the buffer for a complete packet after this start byte
    if start_index != -1 and start_index + 1 + packet_size + 1 <= len(buffer):
        # Read the packet data and check the end byte
        end_index = start_index + 1 + packet_size
        if buffer[end_index:end_index+1] == b'\xfe':
            data = buffer[start_index+1:end_index]
            # Unpack the packet
            try:
                return struct.unpack(packet_format, data)
            except struct.error as e:
                logger.error(f"Error unpacking data: {e}")
        else:
            logger.warning("End byte not found in the latest packet.")
    else:
        logger.warning("No valid packet found.")
    return None
