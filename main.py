#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : Matthew Davidson
# Created Date: 2024-01-01
# version ='0.0.1'
# ---------------------------------------------------------------------------
"""a_short_project_description"""
# ---------------------------------------------------------------------------

import logging
from logging.config import dictConfig
import asyncio

# Import the load_configs function
from config_loader import load_configs

from app_monitor import (
    MonitorManager,
    ProgressBar,
    Table,
    RangeBar,
    TextElement,
    ZeroMQUpdateServer,
    SerialUpdateServer,
    LogMonitor,
)

LOGGING_CONFIG_FILEPATH = "config/logging.yaml"
APP_CONFIG_FILEPATH = "config/application.toml"

# Load user configurations using the config_loader module
configs = load_configs([APP_CONFIG_FILEPATH, LOGGING_CONFIG_FILEPATH])

# Configure logging using the specified logging configuration
dictConfig(configs["logging"])


async def main():
    logging.info(configs["application"])

    # Create a MonitorManager instances
    manager = MonitorManager()

    # Add a progress bar and table elements with formatting
    BAR_WIDTH = 30
    text_format = {"bold": True}
    x_position = TextElement(
        element_id="X_position", text="X: 0.0000", text_format=text_format
    )
    y_position = TextElement(
        element_id="Y_position", text="Y: 0.0000", text_format=text_format
    )
    z_position = TextElement(
        element_id="Z_position", text="Z: 0.0000", text_format=text_format
    )

    [manager.add_element(el) for el in [x_position, y_position, z_position]]

    # Example instantiation of the RangeBar
    axis_properties = dict(
        min_value=-1000,
        max_value=1000,
        # width=50,  # Total width of the bar (e.g., 50 characters)
        bar_format={"fg_color": "green"},  # Custom formatting for the bar (optional)
        text_format={"bold": True},  # Custom formatting for the display text (optional)
        max_label_length=12,  # Maximum length of the label (e.g., 5 characters)
        max_display_length=8,  # Maximum length of the value (e.g., 5 characters)
        marker_trace="█",
        range_trace="-",
    )
    axis_velocity = RangeBar(
        element_id="velocity", label="Axis Vel", unit="m/s", **axis_properties
    )
    axis_torque = RangeBar(
        element_id="torque", label="Axis Torque", unit="Nm", **axis_properties
    )

    logger = LogMonitor(
        element_id="logger",
        timestamp=True,
        timestamp_format="%H:%M:%S.%f",
        timestamp_significant_digits=3,
        border=True,
    )

    axis_group = [axis_velocity, axis_torque]
    manager.add_element_group("X", axis_group)
    manager.add_element_group("Y", axis_group)
    manager.add_element_group("Z", axis_group)

    manager.add_element(logger)

    # Start ZeroMQ manager and subscriber
    server = SerialUpdateServer(
        manager, port="/dev/tty.usbserial-1450", baudrate=115200
    )

    # Create the task to update the monitor manager at a fixed rate
    asyncio.create_task(
        manager.update_at_fixed_rate(interval=0.01)
    )  # Updates every 1 second

    # Start the ZeroMQ subscriber (it will process updates asynchronously)
    await server.start_reader(interval=0.01)


if __name__ == "__main__":
    asyncio.run(main())
