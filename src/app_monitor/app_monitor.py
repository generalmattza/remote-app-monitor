import asyncio


from app_monitor.elements_base import ProgressBar, Table, TextElement
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

    def update(self, element_id, *args):
        """Update an element based on its ID."""
        for element in self.elements:
            if element.element_id == element_id:
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
    # Create a MonitorManager instances
    manager = MonitorManager()

    # Add a progress bar and table elements with formatting
    text = TextElement("Buffers")
    progress_bar1 = ProgressBar("progress_1", total_steps=100)
    table = Table(
        "table_1",
        headers=["1m", "1h", "24h"],
        variables=["Processed", "Errors"],
        data_column_width=6,
    )

    manager.add_element(text)
    manager.add_element(progress_bar1)
    manager.add_element(table)

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
