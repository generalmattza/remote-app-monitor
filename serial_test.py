import struct
import serial

SCALING_FACTOR = 1000  # Same scaling factor as on the Arduino


def read_serial_data(ser):
    while ser.in_waiting:
        start_byte = ser.read(1)
        if start_byte == b"\xAA":  # Check for start byte
            main_var_id = ser.read(1)  # Main variable ID (as byte)
            data_type = ser.read(1)  # Data type byte

            if data_type == b"\x01":  # Fixed-point integer type
                fixed_point_value = struct.unpack("<i", ser.read(4))[
                    0
                ]  # Read 4-byte integer
                value = fixed_point_value / SCALING_FACTOR  # Convert to float
            elif data_type == b"\x02":  # Char array type
                value = b""
                while True:
                    char = ser.read(1)
                    if char == b"\x00":  # Null terminator
                        break
                    value += char
                value = value.decode("utf-8")  # Decode as a UTF-8 string

            params_length = struct.unpack("<B", ser.read(1))[0]  # Params length

            params = []
            if params_length > 0:
                for _ in range(params_length):
                    param_id = ser.read(1)  # Read each param variable ID as a byte
                    params.append(param_id)

            end_byte = ser.read(1)
            if end_byte == b"\xFF":  # Ensure proper packet termination
                data = {
                    "main_var_id": ord(main_var_id),
                    "value": value,
                    "params": [
                        ord(param) for param in params
                    ],  # Will be an empty list if no params
                }
                print(data)
            else:
                print("Error: End byte not found. Invalid packet.")
        else:
            print("Error: Start byte not found. Invalid packet.")


if __name__ == "__main__":

    # Connect to serial port
    # ser = serial.Serial('/dev/ttyUSB0', 9600)
    # Connect to serial port
    ser = serial.Serial("/dev/tty.usbserial-1450", 115200)

    while True:
        read_serial_data(ser)
