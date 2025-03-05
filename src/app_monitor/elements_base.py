from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from tabulate import tabulate
from app_monitor.text_formatter import ANSITextFormatter
from app_monitor.logger import logger

# Maximum width for monitor elements
MAX_MONITOR_WIDTH = 60


# ID generator to create unique IDs for monitor elements
def id_generator(prefix="element"):
    """Generate a unique ID for monitor elements."""
    id_gen = iter(range(9999))
    while True:
        yield f"{prefix}_{next(id_gen)}"


# Base class for all monitor elements
class MonitorElement:
    """Base class for monitor elements like tables and progress bars."""

    id_generator = id_generator("element")

    def __init__(self, element_id=None, border=False, width=MAX_MONITOR_WIDTH, enabled=True):
        """
        Initialize a MonitorElement.

        Args:
            element_id (str): Optional unique ID for the element.
            border (bool): Whether to display a border around the element.
            width (int): Maximum width for the element.
        """
        self.element_id = element_id or self.get_unique_id()
        self.border = border
        self.width = MAX_MONITOR_WIDTH if width is None else width
        self.enabled = enabled
 

    def display(self):
        """Render the monitor element for display."""
        raise NotImplementedError("Subclasses must implement the display method.")

    def update(self, data):
        """Update the monitor element with new data."""
        raise NotImplementedError("Subclasses must implement the update method.")

    def as_dict(self):
        """Return the element as a dictionary."""
        return {self.element_id: self.display()}

    def add_border(self, content):
        """Wrap content in a border if `self.border` is True."""
        if not self.border:
            return content
        lines = content.split("\n")
        width = min(max(len(line) for line in lines) + 4, self.width)
        border_top = "+" + "-" * (width - 2) + "+"
        bordered_content = [f"| {line.ljust(width - 4)} |" for line in lines]
        return "\n".join([border_top] + bordered_content + [border_top])

    def get_unique_id(self):
        """Generate a unique ID for monitor elements."""
        return next(self.id_generator)

    @property
    def value(self):
        raise NotImplementedError("Subclasses must implement the display method.")


# Grouping class for monitor elements
class MonitorGroup(MonitorElement):
    """Class to group monitor elements with hierarchical IDs."""

    id_generator = id_generator("group")

    def __init__(self, group_id, elements=None, border=False, width=MAX_MONITOR_WIDTH, enabled=True):
        """
        Initialize a MonitorGroup.

        Args:
            group_id (str): Unique ID for the group.
            elements (dict): Dictionary of elements to include in the group.
            border (bool): Whether to display a border around the group.
            width (int): Maximum width for the group.
        """
        super().__init__(element_id=group_id, border=border, width=width, enabled=enabled)
        self.group_id = group_id
        self.elements = self.construct_elements(elements)

    def construct_elements(self, elements=None):
        """
        Populate elements with hierarchical IDs.

        Args:
            elements (dict): Original dictionary of elements.

        Returns:
            dict: Dictionary with updated hierarchical IDs.
        """
        if elements is None:
            return {}
        return {
            f"{self.group_id}.{element_id}": element
            for element_id, element in deepcopy(elements).items()
        }

    def add_element(self, element_name, element):
        """
        Add an element to the group with a hierarchical ID.

        Args:
            element_name (str): Name of the element.
            element (MonitorElement): Element instance to add.
        """
        element.element_id = f"{self.group_id}.{element_name}"
        self.elements[element.element_id] = element

    def update_element(self, element_id, *args, **kwargs):
        """
        Update a specific element in the group.

        Args:
            element_id (str): Full ID of the element to update.
        """
        if element_id in self.elements:
            self.elements[element_id].update(*args, **kwargs)

    def display(self):
        """Render the group with its elements."""
        element_displays = "\n".join(
            element.display() for element in self.elements.values()
        )
        return self.add_border(element_displays) if self.border else element_displays

    def get_height(self):
        """Calculate total height including borders and contained elements."""
        element_heights = sum(
            element.get_height() for element in self.elements.values()
        )
        return element_heights + 2 if self.border else element_heights


# Text-based element class
class TextElement(MonitorElement):
    """Class for rendering a text element."""

    id_generator = id_generator("text")

    def __init__(
        self,
        text=None,
        static_text=None,
        element_id=None,
        text_format=None,
        width=MAX_MONITOR_WIDTH,
        enabled=True,
    ):
        """
        Initialize a TextElement.

        Args:
            text (str): Dynamic text to display.
            static_text (str): Static prefix text.
            element_id (str): Optional unique ID for the element.
            text_format (Callable): Formatting function for text.
            width (int): Maximum width for the element.
        """
        super().__init__(element_id, width=width, enabled=enabled)
        self.text = str(text or "")
        self.static_text = static_text
        self.text_format = text_format

    def update(self, text):
        """Update the text element."""
        self.text = str(text)

    def display(self):
        """Render the text element for display."""
        full_text = (self.static_text or "") + self.text
        return (
            self.text_format.format_text(full_text) if self.text_format else full_text
        )

    def get_height(self):
        """Calculate the number of lines the text occupies."""
        return self.text.count("\n") + 1

    @property
    def value(self):
        return self.text


# Progress bar class
class ProgressBar(MonitorElement):
    """Class for rendering a progress bar."""

    id_generator = id_generator("progress")

    def __init__(
        self,
        element_id=None,
        total_steps=10,
        label="Progress",
        width=MAX_MONITOR_WIDTH,
        bar_format=None,
        text_format=None,
        display_value=None,
        max_label_length=None,
        enabled=True,
    ):
        """
        Initialize a ProgressBar.

        Args:
            total_steps (int): Total number of steps for the bar.
            label (str): Label for the progress bar.
            width (int): Maximum width for the bar.
            bar_format (Callable): Formatting function for the bar.
            text_format (Callable): Formatting function for text.
            display_value (str): Optional value to display with the bar.
            max_label_length (int): Maximum length for the label.
        """
        super().__init__(element_id, width=width, enabled=enabled)
        self.total_steps = total_steps
        self.current_step = 0
        self.label = label
        self.bar_format = bar_format
        self.text_format = text_format
        self.display_value = display_value
        self.max_label_length = max_label_length or 10

    def update(self, value, display_value=None):
        """Update the progress bar with a new value."""
        self.current_step = min(float(value), self.total_steps)
        if display_value:
            self.display_value = display_value
        return self.display()

    def display(self):
        """Render the progress bar for display."""
        progress_percentage = self.current_step / self.total_steps
        display_value = (
            self.text_format.format_text(f"{progress_percentage * 100:.1f}%")
            if self.text_format
            else f"{progress_percentage * 100:.1f}%"
        )
        bar_width = self.width - self.max_label_length - len(display_value) - 6
        filled_length = int(bar_width * progress_percentage)
        bar = "█" * filled_length + "░" * (bar_width - filled_length)
        formatted_bar = self.bar_format.format_text(bar) if self.bar_format else bar
        padded_label = self.label.ljust(self.max_label_length)
        return f"{padded_label} [{formatted_bar}] {display_value}"

    def get_height(self):
        """Progress bar occupies one line."""
        return 1

    @property
    def value(self):
        return self.current_step


# Range bar class
class RangeBar(MonitorElement):
    """Class for rendering a range bar with a dynamic marker."""

    id_generator = id_generator("range_bar")

    def __init__(
        self,
        element_id=None,
        min_value=0,
        max_value=100,
        label="Range",
        width=MAX_MONITOR_WIDTH,
        bar_format=None,
        text_format=None,
        display_value=None,
        max_label_length=None,
        max_display_length=None,
        marker_trace="|",
        range_trace="-",
        unit=None,
        scale=1,
        digits=2,
        enabled=True,
    ):
        """
        Initialize a RangeBar.

        Args:
            min_value (float): Minimum value of the range.
            max_value (float): Maximum value of the range.
            label (str): Label for the range bar.
            width (int): Maximum width for the bar.
            bar_format (Callable): Formatting function for the bar.
            text_format (Callable): Formatting function for text.
            display_value (str): Optional value to display with the bar.
            max_label_length (int): Maximum length for the label.
            max_display_length (int): Maximum length for the display value.
            marker_trace (str): Character for the marker.
            range_trace (str): Character for the range bar.
            unit (str): Unit of measurement.
            scale (float): Scaling factor for the values.
            digits (int): Number of decimal places for the display value.
        """
        super().__init__(element_id, width=width, enabled=enabled)
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = (max_value + min_value) / 2
        self.label = label
        self.bar_format = bar_format
        self.text_format = text_format
        self.display_value = display_value
        self.max_label_length = max_label_length or 10
        self.max_display_length = max_display_length or 6
        self.marker_trace = marker_trace
        self.range_trace = range_trace
        self.unit = unit or ""
        self.scale = scale
        self.digits = digits

    def update(self, value, display_value=None):
        """Update the range bar with a new value."""
        self.current_value = max(
            self.min_value, min(float(value) * self.scale, self.max_value)
        )
        if display_value:
            self.display_value = display_value
        return self.display()

    def display(self):
        """Render the range bar for display."""
        progress_ratio = (self.current_value - self.min_value) / (
            self.max_value - self.min_value
        )
        numeric_value = (
            f"{self.current_value:>{self.max_display_length}.{self.digits}f}"
        )
        full_display_value = f"{numeric_value} {self.unit}".ljust(
            self.max_display_length + len(self.unit)
        )
        display_value = (
            self.text_format.format_text(full_display_value)
            if self.text_format
            else full_display_value
        )
        bar_width = self.width - self.max_label_length - self.max_display_length - 13
        marker_position = min(int(bar_width * progress_ratio), bar_width - 1)
        bar = (
            self.range_trace * marker_position
            + self.marker_trace
            + self.range_trace * (bar_width - marker_position - 1)
        )
        formatted_bar = self.bar_format.format_text(bar) if self.bar_format else bar
        padded_label = self.label.ljust(self.max_label_length)
        return f"{padded_label} [{formatted_bar}] {display_value}"

    def get_height(self):
        """Range bar occupies one line."""
        return 1

    @property
    def value(self):
        return self.current_value


# Table class
class Table(MonitorElement):
    """Class for rendering a tabular display."""

    id_generator = id_generator("table")

    def __init__(
        self,
        headers,
        variables,
        element_id=None,
        data_column_width=6,
        left_column_width=None,
        header_format=None,
        column_format=None,
        cell_format=None,
        width=MAX_MONITOR_WIDTH,
        enabled=True,
    ):
        """
        Initialize a Table.

        Args:
            headers (list): List of column headers.
            variables (list): List of row variables.
            data_column_width (int): Width for each data column.
            left_column_width (int): Width for the leftmost column.
            header_format (Callable): Formatting function for headers.
            column_format (Callable): Formatting function for left column.
            cell_format (Callable): Formatting function for data cells.
        """
        super().__init__(element_id, width=width, enabled=enabled)
        self.headers = headers
        self.variables = variables
        self.data = {var: [0] * len(headers) for var in variables}
        self.data_column_width = data_column_width
        self.left_column_width = left_column_width
        self.header_format = header_format
        self.column_format = column_format
        self.cell_format = cell_format

    def update(self, var, header, value):
        """Update the table data for a specific variable and header."""
        if header in self.headers:
            header_index = self.headers.index(header)
            self.data[var][header_index] = value

    def _truncate_or_pad(self, text, width):
        """Ensure text fits within the specified width."""
        text = str(text)
        if len(text) > width:
            return text[: width - 3] + "..."
        return text.center(width)

    def format_row(self, left_cell, row):
        """Format a row with appropriate column widths."""
        left_cell = (
            self._truncate_or_pad(left_cell, self.left_column_width)
            if self.left_column_width
            else left_cell
        )
        formatted_data_cells = [
            self._truncate_or_pad(cell, self.data_column_width) for cell in row
        ]
        return [left_cell] + formatted_data_cells

    def display(self):
        """Render the table for display."""
        centered_headers = [
            self._truncate_or_pad(header, self.data_column_width)
            for header in self.headers
        ]
        formatted_headers = self.format_row("", centered_headers)
        rows = [self.format_row(var, self.data[var]) for var in self.variables]
        return tabulate(rows, headers=formatted_headers, tablefmt="fancy_grid")

    def get_height(self):
        """Calculate the height of the table."""
        return len(self.variables) + 2


# Log monitor class
class LogMonitor(MonitorElement):
    """Class for rendering a log monitor."""

    id_generator = id_generator("log")

    def __init__(
        self,
        element_id=None,
        max_logs=10,
        log_format=None,
        timestamp=False,
        timestamp_format="%Y-%m-%d %H:%M:%S.%f",
        timestamp_significant_digits=7,
        border=False,
        width=MAX_MONITOR_WIDTH,
        header="Log Monitor",
        enabled=True,
    ):
        """
        Initialize a LogMonitor.

        Args:
            max_logs (int): Maximum number of logs to display.
            log_format (Callable): Formatting function for logs.
            timestamp (bool): Whether to include a timestamp.
            timestamp_format (str): Format for the timestamp.
            timestamp_significant_digits (int): Digits to truncate from the timestamp.
            header (str): Header for the log monitor.
        """
        super().__init__(element_id, border=border, width=width, enabled=enabled)
        self.max_logs = max_logs
        self.logs = []
        self.log_format = log_format
        self.timestamp = timestamp
        self.timestamp_format = timestamp_format
        self.timestamp_significant_digits = timestamp_significant_digits
        self.header = header

    def update(self, log):
        """Update the log monitor with a new log entry."""
        if self.timestamp:
            timestamp = datetime.now().strftime(self.timestamp_format)
            timestamp = timestamp[: -self.timestamp_significant_digits]
            log = f"{timestamp} {log}"
        self.logs.append(log)
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)

    def display(self):
        """Render the log monitor for display."""
        formatted_logs = [log.ljust(self.width - 4) for log in self.logs]
        while len(formatted_logs) < self.max_logs:
            formatted_logs.append(" " * (self.width - 4))
        content = "\n".join(formatted_logs)
        return self.add_border(content)

# Indicator lamp class
class IndicatorLamp(MonitorElement):
    """Class for rendering an indicator lamp."""

    id_generator = id_generator("lamp")

    def __init__(
        self,
        element_id=None,
        label="Lamp",
        on_color="green",
        off_color="red",
        width=MAX_MONITOR_WIDTH,
        enabled=True,
    ):
        """
        Initialize an IndicatorLamp.

        Args:
            label (str): Label for the lamp.
            on_color (str): Color when the lamp is on.
            off_color (str): Color when the lamp is off.
        """
        super().__init__(element_id, width=width, enabled=enabled)
        self.label = label
        self.on_color = on_color
        self.off_color = off_color
        self.state = False

    def update(self, state):
        """Update the lamp's state."""
        self.state = bool(state)

    def display(self):
        """Render the indicator lamp for display."""
        color = self.on_color if self.state else self.off_color

        # Use ANSITextFormatter to apply color formatting
        formatter = ANSITextFormatter(
            text="●",
            fg_color=color,  # Apply color
            bold=True,  # Ensure visibility
        )

        formatted_lamp = formatter.format_text()
        return f"{self.label}: {formatted_lamp}".ljust(MAX_MONITOR_WIDTH)

    @property
    def value(self):
        return int(self.state)
    

if __name__ == "__main__":
    # Example usage of the MonitorElement classes
    monitor = MonitorGroup(monitor = "monitor")
