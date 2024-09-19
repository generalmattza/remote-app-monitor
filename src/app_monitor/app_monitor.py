import sys
import time
import zmq
import threading
from tabulate import tabulate
from text_formatter import format_text
from banner import banner_metrics_manager as BANNER

MAX_MONITOR_WIDTH = 40


def format_list(items, format_options=None):
    """Format a list of values as strings with optional formatting."""
    if format_options:
        return [format_text(str(item), **format_options) for item in items]
    return [str(item) for item in items]


class MonitorElement:
    """Base class for monitor elements like tables and progress bars."""

    def __init__(self, element_id):
        self.element_id = element_id  # Assign a unique ID to each element

    def display(self):
        raise NotImplementedError("Subclasses must implement the display method")

    def update(self, data):
        """Update element with data."""
        raise NotImplementedError("Subclasses must implement the update method")

    def get_height(self):
        """Return the height of the element in lines."""
        raise NotImplementedError("Subclasses must implement the get_height method")


class ProgressBar(MonitorElement):
    """Class for rendering a progress bar."""

    def __init__(
        self,
        element_id,
        total_steps,
        width=MAX_MONITOR_WIDTH,
        bar_format=None,
        text_format=None,
    ):
        super().__init__(element_id)
        self.total_steps = total_steps
        self.current_step = 0
        self.width = width

        # Store formatting options for the progress bar itself and the text
        self.bar_format = bar_format
        self.text_format = text_format

    def update(self, progress):
        """Update progress bar based on the current progress percentage."""
        self.current_step = float(progress)
        return self.display()

    def display(self):
        """Generate the progress bar for display."""
        progress_percentage = self.current_step / self.total_steps
        bar_width = self.width - 10
        filled_length = int(bar_width * progress_percentage)
        bar = "█" * filled_length + "░" * (bar_width - filled_length)

        # Format the progress bar and the percentage text if formats are provided
        formatted_bar = format_text(bar, **self.bar_format) if self.bar_format else bar
        formatted_percentage = (
            format_text(f"{progress_percentage * 100:.1f}%", **self.text_format)
            if self.text_format
            else f"{progress_percentage * 100:.1f}%"
        )

        return f"Buffer [{formatted_bar}] {formatted_percentage}"

    def get_height(self):
        """Progress bar only occupies one line."""
        return 1


class Table(MonitorElement):
    """Class for rendering a table."""

    def __init__(
        self,
        element_id,
        headers,
        variables,
        data_column_width=6,
        left_column_width=None,
        header_format=None,
        column_format=None,
        cell_format=None,
    ):
        super().__init__(element_id)
        self.headers = headers
        self.variables = variables
        self.data = {var: [0] * len(headers) for var in variables}
        self.data_column_width = data_column_width  # Set equal width for data columns
        self.left_column_width = left_column_width  # Set the width for the leftmost column, or None for flexible width

        # Store formatting options for headers, columns, and cells
        self.header_format = header_format
        self.column_format = column_format
        self.cell_format = cell_format

    def update(self, var, header, value):
        """Update the table data for a given variable and header."""
        if header in self.headers:
            header_index = self.headers.index(header)
            self.data[var][header_index] = value

    def _truncate_or_pad(self, text, width):
        """Ensure that the text fits into the specified width by padding or truncating."""
        text = str(text)
        if len(text) > width:
            return text[: width - 3] + "..."  # Truncate and add ellipsis if too long
        return text.center(width)  # Center-align text

    def format_row(self, left_cell, row):
        """Format the left column and data cells to ensure proper column widths."""
        # If left_column_width is specified, apply it; otherwise, use the full width of the left_cell
        if self.left_column_width:
            left_cell = self._truncate_or_pad(left_cell, self.left_column_width)

        # Apply the data column width to the rest of the cells, with optional formatting
        formatted_data_cells = [
            (
                format_text(
                    self._truncate_or_pad(cell, self.data_column_width),
                    **self.cell_format,
                )
                if self.cell_format
                else self._truncate_or_pad(cell, self.data_column_width)
            )
            for cell in row
        ]
        formatted_left_cell = (
            format_text(left_cell, **self.column_format)
            if self.column_format
            else left_cell
        )
        return [formatted_left_cell] + formatted_data_cells

    def display(self):
        """Generate a table for display with centered headers and formatted data."""
        # Center-align and format the headers
        centered_headers = [
            (
                format_text(
                    self._truncate_or_pad(header, self.data_column_width),
                    **self.header_format,
                )
                if self.header_format
                else self._truncate_or_pad(header, self.data_column_width)
            )
            for header in self.headers
        ]

        # Format the headers and data rows
        formatted_headers = self.format_row(
            "", centered_headers
        )  # Center and format the headers
        rows = [
            self.format_row(
                format_text(var, **self.column_format) if self.column_format else var,
                [self.data[var][i] for i in range(len(self.headers))],
            )
            for var in self.variables
        ]
        # Ensure both headers and data cells are center-aligned except the leftmost column
        return tabulate(
            rows,
            headers=formatted_headers,
            tablefmt="fancy_grid",
            colalign=["left"] + ["center"] * len(self.headers),
        )

    def get_height(self):
        """Calculate the number of lines the table occupies."""
        return len(self.variables) + 2  # Number of rows + 2 for the header and border


class MonitorManager:
    """Main class to manage all monitor elements and updates using double buffering."""

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
        sys.stdout.write("\n".join(self.buffer) + "\n")
        sys.stdout.flush()

    def clear_monitor(self):
        """Clear the monitor screen."""
        sys.stdout.write("\033[2J\033[H")  # Clear screen and move cursor to top left
        sys.stdout.flush()


class ZeroMQUpdateManager:
    """Class to manage updates via ZeroMQ PUB-SUB pattern."""

    def __init__(self, monitor_manager, host="localhost", port=5556):
        self.monitor_manager = monitor_manager
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)  # Subscriber socket
        self.socket.connect(f"tcp://{self.host}:{self.port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

    def start_subscriber(self):
        """Start the ZeroMQ subscriber."""
        print(f"Subscribed to {self.host}:{self.port}")
        while True:
            message = self.socket.recv_string()
            self.process_update(message)

    def process_update(self, message):
        """Process updates received via ZeroMQ."""
        try:
            # Assuming message is in the format: "element_id var header value"
            update_info = message.split()
            element_id = update_info[0]
            update_args = update_info[1:]
            self.monitor_manager.update(element_id, *update_args)
            self.monitor_manager.display_all()
        except Exception as e:
            print(f"Error processing update: {e}", file=sys.stderr)


# Example usage
if __name__ == "__main__":
    # Create a MonitorManager instance
    manager = MonitorManager()

    # Add elements with unique IDs
    progress_bar = ProgressBar(
        "progress_1",
        total_steps=100,
        width=40,
        bar_format={"fg_color": "blue"},
    )
    table = Table(
        "table_1",
        headers=["1m", "1h", "24h"],
        variables=["Processed", "Errors"],
        # header_format={"bold": True, "fg_color": "cyan"},
        column_format={"bold": True, "fg_color": "red"},
        cell_format={"fg_color": "white"},
    )

    manager.add_element(progress_bar)
    manager.add_element(table)
    manager.display_all()

    # # Simulate some local updates
    # for i in range(10):
    #     manager.update("progress_1", i + 1)
    #     manager.update("table_1", "Processed", "1m", i + 1)
    #     manager.display_all()
    #     time.sleep(0.5)

    # Start ZeroMQ subscriber for remote updates
    zmq_manager = ZeroMQUpdateManager(manager)
    threading.Thread(target=zmq_manager.start_subscriber).start()
