#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2024-01-01
# version ='0.0.1'
# ---------------------------------------------------------------------------
"""a_short_module_description"""
# ---------------------------------------------------------------------------

import shutil
import sys
import time
from tabulate import tabulate
from text_formatter import format_text

MAX_TERMINAL_WIDTH = 40


def format_list(items, format_options=None):
    """Format a list of values as strings with optional formatting."""
    if format_options:
        return [format_text(str(item), **format_options) for item in items]
    return [str(item) for item in items]


banner = """
___  ___     _        _           ___  ___                                  
|  \/  |    | |      (_)          |  \/  |                                  
| .  . | ___| |_ _ __ _  ___ ___  | .  . | __ _ _ __   __ _  __ _  ___ _ __ 
| |\/| |/ _ \ __| '__| |/ __/ __| | |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
| |  | |  __/ |_| |  | | (__\__ \ | |  | | (_| | | | | (_| | (_| |  __/ |   
\_|  |_/\___|\__|_|  |_|\___|___/ \_|  |_/\__,_|_| |_|\__,_|\__, |\___|_|   
                                                             __/ |          
                                                            |___/           
"""


class TerminalAppInfo:
    def __init__(self, variables, durations, banner=None):
        self.variables = variables
        self.durations = durations
        self.table = {var: [0] * len(durations) for var in variables}
        self.total_steps = len(variables) * len(durations)
        self.current_step = 0
        self.banner = banner

    def display_banner(self, format=None):
        """Display banner."""
        if format:
            banner_text = format_text(self.banner, **format)
        else:
            banner_text = self.banner
        sys.stdout.write(banner_text)
        sys.stdout.flush()

    def update(self, var, duration, value):
        """Update the table with new values and display progress."""
        if duration not in self.durations:
            print(f"Unknown duration: {duration}", file=sys.stderr)
            return

        duration_index = self.durations.index(duration)
        self.table[var][duration_index] = value
        self.current_step += 1
        progress_percentage = (self.current_step / self.total_steps) * 100

        # Get terminal width dynamically
        terminal_width = min(shutil.get_terminal_size().columns, MAX_TERMINAL_WIDTH)

        # Clear the terminal screen before printing the updated table
        self.clear_terminal()

        if self.show_banner:
            self.display_banner(banner)

        # Display the progress bar and table
        sys.stdout.write(f"Progress: {progress_percentage:.2f}%\n")
        sys.stdout.write(
            self.progress_bar(progress_percentage / 100, terminal_width) + "\n"
        )
        sys.stdout.write(
            self.format_table(header_format={"fg_color": "red", "bold": True}) + "\n"
        )
        sys.stdout.flush()

    def format_table(self, header_format=None, column_format=None, cell_format=None):
        """Format the table for display using tabulate."""
        headers = (
            [""] + format_list(self.durations, header_format)
            if header_format
            else [""] + self.durations
        )
        rows = [
            [format_text(var, column_format) if column_format else var]
            + [
                format_text(cell, cell_format) if cell_format else cell
                for cell in self.table[var]
            ]
            for var in self.variables
        ]
        return tabulate(
            rows,
            headers=headers,
            tablefmt="fancy_grid",
            colalign=["center"] * len(headers),
        )

    def progress_bar(self, progress, width, format_options=None):
        """Generate a progress bar with optional formatting."""
        bar_width = width - 10
        filled_length = int(bar_width * progress)
        bar = "█" * filled_length + "░" * (bar_width - filled_length)
        return f"Buffer [{format_text(bar, **format_options) if format_options else bar}] {progress * 100:.1f}%"

    def clear_terminal(self):
        """Clear the terminal screen."""
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def done(self):
        """Display completion message."""
        sys.stdout.write("\nProcess completed!\n")
        sys.stdout.flush()


# Example usage
if __name__ == "__main__":
    variables = ["Processed", "Errors"]
    durations = ["1m", "1h", "24h"]

    updater = TerminalStatusUpdaterWithTable(variables, durations)

    for i, var in enumerate(variables):
        for j, duration in enumerate(durations):
            updater.update(var, duration, (i + 1) * (j + 1))  # Simulated values
            time.sleep(0.5)  # Simulate processing time

    updater.done()
