import asyncio
from copy import deepcopy

from app_monitor.elements_base import (
    ProgressBar,
    Table,
    TextElement,
    RangeBar,
    MonitorGroup,
)
from app_monitor.server import ZeroMQUpdateServer

import logging

logger = logging.getLogger(__name__)


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
        group_elements = {
            f"{group_id}.{element.element_id}": element for element in elements
        }
        group = MonitorGroup(group_id=group_id, elements=group_elements, border=True)
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

    def display_all(self):
        """Construct the full screen content in a buffer and then display it."""
        self.buffer = []  # Clear the buffer for the new frame

        for element in self.elements:
            self.buffer.append(
                element.display()
            )  # Add each element's display to the buffer

        self.flush_buffer_to_screen()

    def flush_buffer_to_screen(self):
        """Clear the terminal and write the buffer contents to the screen."""
        self.clear_monitor()

        # Print the entire buffered content at once
        print("\n".join(self.buffer))

    def clear_monitor(self):
        """Clear the monitor screen."""
        print("\033[2J\033[H")  # Clear screen and move cursor to top left

    async def update_at_fixed_rate(self, interval=1):
        """Asynchronously update the monitor at a fixed rate."""
        while True:
            self.display_all()  # Display the current metrics
            await asyncio.sleep(interval)  # Wait for the next update cycle


async def main():
    # Create a MonitorManager instance
    manager = MonitorManager()

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
