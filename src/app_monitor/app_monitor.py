import asyncio
from copy import deepcopy
import sys

from app_monitor.elements_base import (
    ProgressBar,
    Table,
    TextElement,
    RangeBar,
    MonitorGroup,
)
from app_monitor.server import ZeroMQUpdateServer

from .logger import logger


class MonitorManager:
    """Main class to manage all monitor elements and updates asynchronously."""

    def __init__(self):
        self.elements = []  # Store elements as a list to maintain their order
        self.buffer = []  # The off-screen buffer where all elements are written

    def add_element(self, element):
        """Add a monitor element to the manager."""
        self.elements.append(element)

    def add_element_group(self, group_id, elements):
        """Add a group of elements to the manager by creating a MonitorGroup."""
        # Automatically set hierarchical IDs based on the group_id
        group = MonitorGroup(group_id=group_id, elements=elements, border=True)
        self.elements.append(group)  # Add the whole group as one element

    def update(self, element_id, *args):
        """Update an element or an element within a group based on its full hierarchical ID."""
        for element in self.elements:
            if isinstance(element, MonitorGroup):
                # Check if the element_id is within the group's elements
                if element_id in element.elements:
                    element.update_element(element_id, *args)
                    break
            elif element.element_id == element_id:
                element.update(*args)
                break

    def generate_element_id_map(self):
        """Generate a list of all element IDs in the monitor manager."""
        element_count = 0

        def _element_id_generator(elements):
            """Recursively generate element IDs."""
            nonlocal element_count
            for element in elements:
                if isinstance(element, MonitorGroup):
                    yield from _element_id_generator(element.elements.values())
                else:
                    yield element_count, element.element_id
                    element_count += 1

        return {
            str(number): element_id
            for number, element_id in _element_id_generator(self.elements)
        }


class TerminalManager(MonitorManager):

    def update_screen_buffer(self):
        """Construct the full screen content in a buffer"""
        self.buffer = []  # Clear the buffer for the new frame

        for element in self.elements:
            self.buffer.append(
                element.display()
            )  # Add each element's display to the buffer

    def update_screen(self):
        """Clear the terminal and write the buffer contents to the screen."""
        self.clear_monitor()
        # Print the entire buffered content at once
        sys.stdout.write("\n".join(self.buffer))

    def clear_monitor(self):
        """Clear the monitor screen."""
        sys.stdout.write("\033[2J\033[H")  # Clear screen and move cursor to top left

    async def update_screen_fixed_rate(self, frequency=1):
        """Asynchronously update the monitor at a fixed rate."""
        assert frequency > 0, "Frequency must be greater than 0."
        while True:
            self.update_screen()  # Display the current metrics
            await asyncio.sleep(1 / frequency)  # Wait for the next update cycle

    async def update_screen_buffer_fixed_rate(self, frequency=1):
        """Asynchronously update all elements at a fixed rate."""
        assert frequency > 0, "Frequency must be greater than 0."
        while True:
            self.update_screen_buffer()
            await asyncio.sleep(1 / frequency)

    async def update_fixed_rate(self, frequency=30):
        await asyncio.gather(
            self.update_screen_fixed_rate(frequency=frequency),
            self.update_screen_buffer_fixed_rate(frequency=frequency),
        )


import asyncio
import json
from flask_socketio import SocketIO


class SocketManager(MonitorManager):
    """Subclass of MonitorManager that adds functionality to push data to a WebSocket."""

    def __init__(self, socketio: SocketIO, frequency=1):
        """
        Initialize with a SocketIO instance and a push frequency.

        :param socketio: SocketIO instance to handle WebSocket communication.
        :param frequency: Frequency in Hz for pushing updates to clients.
        """
        super().__init__()  # Initialize the parent MonitorManager
        self.socketio = socketio
        self.frequency = frequency

    def to_json(self):
        """Convert all monitor elements to JSON format."""
        data = []
        for element in self.elements:
            if isinstance(element, MonitorGroup):
                raise NotImplementedError(
                    "MonitorGroup is not supported in JSON format."
                )
            else:
                data.append(element.as_dict())
        # Merge and flatten all element dict objects into a single JSON object
        data = {key: value for element in data for key, value in element.items()}
        return json.dumps(data)

    async def push_data(self):
        """Asynchronously push data to all connected WebSocket clients at the specified frequency."""
        while True:
            data = self.to_json()  # Get data in JSON format
            self.socketio.emit("update", data)  # Push data to WebSocket clients
            await asyncio.sleep(1 / self.frequency)  # Control push frequency

    def set_frequency(self, frequency):
        """Set the frequency at which data is pushed to clients."""
        assert frequency > 0, "Frequency must be greater than 0."
        self.frequency = frequency


async def main():
    # Create a MonitorManager instance
    manager = TerminalManager()

    # Add a text element and a progress bar
    text = TextElement("Buffers")
    progress_bar1 = ProgressBar("progress_1", total_steps=100)
    manager.add_element(text)
    manager.add_element(progress_bar1)

    # Add a group of RangeBars (velocity and torque) for axis X
    velocity = RangeBar(element_id="velocity", label="Velocity")
    torque = RangeBar(element_id="torque", label="Torque")
    manager.add_element_group("X", [velocity, torque])

    # Update elements within the group
    manager.update("X.velocity", 50)
    manager.update("X.torque", 75)

    # Start ZeroMQ manager and subscriber
    zmq_server = ZeroMQUpdateServer(manager)

    # Create the task to update the monitor manager at a fixed rate
    asyncio.create_task(
        manager.update_at_fixed_rate(interval=1 / 30)
    )  # Updates every 1 second

    # Start the ZeroMQ subscriber (it will process updates asynchronously)
    await zmq_server.start_subscriber()


if __name__ == "__main__":
    asyncio.run(main())
