# Remote App Monitor

`remote-app-monitor` is a Python-based tool designed to facilitate remote monitoring of applications by creating and managing monitor elements like progress bars, tables, and range bars. It allows for efficient, customizable data visualization and monitoring from both serial and ZeroMQ data sources.

## Features

- **Modular Monitors**: Configure multiple monitor elements such as RangeBars, Log Monitors, and Tables.
- **Group Functionality**: Group elements under specific IDs for easy reference and enhanced organization (e.g., `X.velocity`, `X.torque`).
- **Asynchronous Updating**: Updates monitored data asynchronously at a set rate, independent of data input frequency.
- **Serial and ZeroMQ Communication**: Supports both serial and ZeroMQ data sources, enabling flexible data streaming.
- **ANSI-Formatted Terminal Output**: Customize terminal output with ANSI colors and formatting for clear visual differentiation.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/davidson-engineering/remote-app-monitor.git
   cd remote-app-monitor
   ```

2. **Install Dependencies**:
   Make sure you have Python 3.7+ installed, then install dependencies:
   ```bash
   pip install .
   ```

## Usage

### Basic Setup

1. **Initialize the Monitor**:
   ```python
   from remote_app_monitor import Monitor

   monitor = Monitor()
   ```

2. **Add Monitor Elements**:
   Add various monitor elements like `RangeBar`, `LogMonitor`, or `Table` with unique IDs:
   ```python
   monitor.add_range_bar("X.velocity", min_val=0, max_val=100)
   monitor.add_log("X.torque", timestamp=True)
   monitor.add_table("system_status")
   ```

3. **Start Monitoring**:
   Start the monitor asynchronously. Data can then be sent to update each element.
   ```python
   monitor.start()
   ```

### Serial Server

The `remote-app-monitor` includes a **Serial Server** to handle communication with serial devices, enabling real-time monitoring from an Arduino or similar microcontroller. The Serial Server is optimized for speed, using a custom protocol to minimize overhead.

1. **Initialize the Serial Server**:
   ```python
   from remote_app_monitor import SerialServer

   serial_server = SerialServer(port='COM3', baudrate=9600)
   monitor.add_server(serial_server)
   ```

2. **Start Serial Communication**:
   Once the Serial Server is added, the monitor will handle incoming data:
   ```python
   serial_server.start()
   ```

3. **Updating Elements via Serial**:
   Data packets received over serial should match the monitor element IDs (e.g., `X.velocity`, `X.torque`). The Serial Server will parse and update the respective elements.

### ZeroMQ Server

`remote-app-monitor` also includes a **ZeroMQ Server** to support scalable data communication through a PUB-SUB pattern, ideal for real-time, remote monitoring from multiple data sources.

1. **Initialize the ZeroMQ Server**:
   ```python
   from remote_app_monitor import ZeroMQServer

   zmq_server = ZeroMQServer("tcp://localhost:5555")
   monitor.add_server(zmq_server)
   ```

2. **Start ZeroMQ Communication**:
   Similar to the Serial Server, the ZeroMQ server will handle incoming data from remote publishers:
   ```python
   zmq_server.start()
   ```

3. **Publishing Data to ZeroMQ**:
   From a remote data source, publish updates that match monitor element IDs (e.g., `X.velocity`, `X.torque`). ZeroMQ will parse and distribute the data to the correct elements.

### Example: Grouping Elements

Elements can be grouped under an ID to allow for structured, hierarchical monitoring. For example, `X` could represent an axis, with `X.velocity` and `X.torque` representing specific monitored metrics:

```python
monitor.add_range_bar("X.velocity", min_val=0, max_val=100)
monitor.add_range_bar("X.torque", min_val=0, max_val=500)
monitor.add_log("X.status", timestamp=True)
```

## Customization

Each monitor element can be customized with parameters during initialization:

- **RangeBar**: Configure min/max values, colors, and update frequency.
- **LogMonitor**: Set timestamps, log format, and custom colors.
- **Table**: Define columns, row structure, and update formats.

## License

This project is licensed under the MIT License.
