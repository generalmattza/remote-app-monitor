from tabulate import tabulate


MAX_MONITOR_WIDTH = 40

from app_monitor.text_formatter import format_text


def id_generator(prefix="element"):
    """Generate a unique ID for monitor elements."""
    id_generator = iter(range(9999))
    while True:
        yield f"{prefix}_{next(id_generator)}"


class MonitorElement:
    """Base class for monitor elements like tables and progress bars."""

    id_generator = id_generator("element")

    def __init__(self, element_id=None):
        self.element_id = (
            element_id or self.get_unique_id()
        )  # Assign a unique ID to each element

    def display(self):
        raise NotImplementedError("Subclasses must implement the display method")

    def update(self, data):
        """Update element with data."""
        raise NotImplementedError("Subclasses must implement the update method")

    def get_unique_id(self):
        """Generate a unique ID for monitor elements."""
        return next(self.id_generator)


class TextElement(MonitorElement):
    """Class for rendering a text element."""

    id_generator = id_generator("text")

    def __init__(self, text, element_id=None, text_format=None):
        super().__init__(element_id)
        self.text = text
        self.text_format = text_format

    def update(self, text):
        """Update the text element with new text."""
        self.text = text

    def display(self):
        """Generate the text element for display."""
        return (
            format_text(self.text, **self.text_format)
            if self.text_format
            else self.text
        )

    def get_height(self):
        """Calculate the number of lines the text element occupies."""
        return self.text.count("\n") + 1


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
    ):
        super().__init__(element_id)
        self.total_steps = total_steps
        self.current_step = 0
        self.width = width

        self.label = label
        self.display_value = display_value
        self.max_label_length = (
            max_label_length or 10
        )  # Maximum label length to fit the progress bar

        # Store formatting options for the progress bar itself and the text
        self.bar_format = bar_format
        self.text_format = text_format

    def update(self, value, display_value=None):
        """Update progress bar based on the current progress percentage."""
        self.current_step = min(float(value), self.total_steps)
        if display_value:
            self.display_value = display_value
        return self.display()

    def display(self):
        """Generate the progress bar for display."""
        progress_percentage = self.current_step / self.total_steps
        bar_width = self.width - 10
        filled_length = int(bar_width * progress_percentage)
        bar = "█" * filled_length + "░" * (bar_width - filled_length)

        # Format the progress bar and the percentage text if formats are provided
        formatted_bar = format_text(bar, **self.bar_format) if self.bar_format else bar
        if self.display_value is None:
            display_value = (
                format_text(f"{progress_percentage * 100:.1f}%", **self.text_format)
                if self.text_format
                else f"{progress_percentage * 100:.1f}%"
            )
        else:
            display_value = self.display_value

        padded_label = self.label.ljust(self.max_label_length)

        return f"{padded_label} [{formatted_bar}] {display_value}"

    def get_height(self):
        """Progress bar only occupies one line."""
        return 1


class RangeBar(MonitorElement):
    """Class for rendering a range bar with min/max and a dynamic current value marker."""

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
        marker_trace="|",
        range_trace="-",
    ):
        super().__init__(element_id)
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = (max_value + min_value) / 2
        self.width = width
        self.label = label
        self.display_value = display_value
        self.max_label_length = max_label_length or 10
        self.marker_trace = marker_trace
        self.range_trace = range_trace

        # Store formatting options for the bar itself and the text
        self.bar_format = bar_format
        self.text_format = text_format

    def update(self, value, display_value=None):
        """Update range bar based on the current value within the range."""
        self.current_value = max(self.min_value, min(float(value), self.max_value))
        if display_value:
            self.display_value = display_value
        return self.display()

    def display(self):
        """Generate the range bar for display."""
        # Calculate the proportion of the current value in the range
        progress_ratio = (self.current_value - self.min_value) / (
            self.max_value - self.min_value
        )
        bar_width = self.width - 10
        marker_position = int(bar_width * progress_ratio)

        # Create the bar with a marker at the current position
        bar = (
            self.range_trace * marker_position
            + self.marker_trace
            + self.range_trace * (bar_width - marker_position - 1)
        )

        # Format the range bar and the current value if formats are provided
        formatted_bar = format_text(bar, **self.bar_format) if self.bar_format else bar
        display_value = (
            (
                format_text(f"{self.current_value}", **self.text_format)
                if self.text_format
                else f"{self.current_value}"
            )
            if self.display_value is None
            else self.display_value
        )

        padded_label = self.label.ljust(self.max_label_length)

        return f"{padded_label} [{formatted_bar}] {display_value}"

    def get_height(self):
        """Range bar only occupies one line."""
        return 1


class Table(MonitorElement):
    """Class for rendering a table."""

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
