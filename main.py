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
    text = TextElement(element_id="text_0", text="*** Buffers ***")

    database_buffer_fill = ProgressBar(
        element_id="database_buffer_fill",
        label="Database",
        total_steps=1000,
        width=BAR_WIDTH,
    )
    processing_buffer_fill = ProgressBar(
        element_id="processing_buffer_fill",
        label="Processing",
        total_steps=1000,
        width=BAR_WIDTH,
        bar_format=dict(fg_color="blue"),
    )
    table = Table(
        element_id="metrics_processed",
        headers=["Count"],
        variables=["Processed", "Errors"],
        data_column_width=6,
    )

    # Example instantiation of the RangeBar
    axis_properties = dict(
        min_value=-100,
        max_value=100,
        width=50,  # Total width of the bar (e.g., 50 characters)
        bar_format={"fg_color": "green"},  # Custom formatting for the bar (optional)
        text_format={"bold": True},  # Custom formatting for the display text (optional)
        max_label_length=12,  # Maximum length of the label (e.g., 5 characters)
        marker_trace="█",
        range_trace="-",
    )
    x_axis_position = RangeBar(
        element_id="x_pos", label="X-axis Pos", **axis_properties
    )
    x_axis_velocity = RangeBar(
        element_id="x_vel", label="X-axis Vel", **axis_properties
    )
    x_axis_acceleration = RangeBar(
        element_id="x_acc", label="X-axis Acc", **axis_properties
    )
    y_axis_position = RangeBar(
        element_id="y_pos", label="Y-axis Pos", **axis_properties
    )
    y_axis_velocity = RangeBar(
        element_id="y_vel", label="Y-axis Vel", **axis_properties
    )
    y_axis_acceleration = RangeBar(
        element_id="y_acc", label="Y-axis Acc", **axis_properties
    )
    z0_axis_position = RangeBar(
        element_id="z0_pos", label="Z0-axis Pos", **axis_properties
    )
    z0_axis_velocity = RangeBar(
        element_id="z0_vel", label="Z0-axis Vel", **axis_properties
    )
    z0_axis_acceleration = RangeBar(
        element_id="z0_acc", label="Z0-axis Acc", **axis_properties
    )
    z1_axis_position = RangeBar(
        element_id="z1_pos", label="Z1-axis Pos", **axis_properties
    )
    z1_axis_velocity = RangeBar(
        element_id="z1_vel", label="Z1-axis Vel", **axis_properties
    )
    z1_axis_acceleration = RangeBar(
        element_id="z1_acc", label="Z1-axis Acc", **axis_properties
    )

    elements = [
        x_axis_position,
        x_axis_velocity,
        x_axis_acceleration,
        y_axis_position,
        y_axis_velocity,
        y_axis_acceleration,
        z0_axis_position,
        z0_axis_velocity,
        z0_axis_acceleration,
        z1_axis_position,
        z1_axis_velocity,
        z1_axis_acceleration,
    ]

    [manager.add_element(el) for el in elements]

    # Start ZeroMQ manager and subscriber
    zmq_server = ZeroMQUpdateServer(manager)

    # Create the task to update the monitor manager at a fixed rate
    asyncio.create_task(
        manager.update_at_fixed_rate(interval=0.02)
    )  # Updates every 1 second

    # Start the ZeroMQ subscriber (it will process updates asynchronously)
    await zmq_server.start_subscriber()


if __name__ == "__main__":
    asyncio.run(main())
