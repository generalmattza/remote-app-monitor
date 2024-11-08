import serial
import struct


class SerialReader:
    def __init__(self, serial_connection):
        self.ser = serial_connection

    def read_data(self):
        if self.ser.in_waiting:
            return self.ser.read(self.ser.in_waiting)
        return b""


class AppMonitorReader(SerialReader):
    SCALING_FACTOR = 1000  # Same scaling factor as on the Arduino

    def __init__(self, serial_connection, dict_encoding_map=None):
        super().__init__(serial_connection)
        self.dict_encoding_map = dict_encoding_map or {}

    def decode_value(self, encoded_value):
        """
        Decodes a single byte value using the dictionary encoding map.
        """
        return self.dict_encoding_map.get(encoded_value, encoded_value)

    def read_data(self):
        raw_data = super().read_data()

        if not raw_data:
            return

        index = 0
        while index < len(raw_data):
            if raw_data[index] == 0xAA:  # Start byte
                index += 1

                # Ensure we have enough bytes for the minimum packet length
                if index + 6 > len(raw_data):
                    print("Error: Incomplete packet.")
                    return

                # Extract element ID and data type
                element_id = raw_data[index]
                data_type = raw_data[index + 1]
                index += 2

                # Decode the value based on data type
                if data_type == 0x01:  # Fixed-point integer type
                    fixed_point_value = struct.unpack_from("<i", raw_data, index)[0]
                    value = fixed_point_value / self.SCALING_FACTOR
                    index += 4
                elif data_type == 0x02:  # Char array type
                    value = b""
                    while index < len(raw_data) and raw_data[index] != 0x00:
                        value += bytes([raw_data[index]])
                        index += 1
                    value = value.decode("utf-8")
                    index += 1  # Skip null terminator
                else:
                    print(f"Error: Unknown data type {data_type}.")
                    return

                # Read params length and params
                params_length = raw_data[index]
                index += 1
                params = []
                for _ in range(params_length):
                    if index < len(raw_data):
                        params.append(raw_data[index])
                        index += 1
                    else:
                        print("Error: Incomplete params data.")
                        return

                # Check for end byte
                if index < len(raw_data) and raw_data[index] == 0xFF:
                    index += 1  # Move past end byte
                    data = {
                        "element_id": self.decode_value(element_id),
                        "value": value,
                        "params": [self.decode_value(param) for param in params],
                    }
                    return self.process_data(data)
                else:
                    print("Error: End byte not found. Invalid packet.")
            else:
                print("Error: Start byte not found.")
                break

    def process_data(self, data):
        """
        Process the decoded data.
        """
        return data


class DecoderWithDictionary:
    def __init__(self, dict_encoding_map):
        """
        Initializes the decoder with a dictionary encoding map.

        :param dict_encoding_map: Dictionary mapping byte values to human-readable names.
        """
        self.dict_encoding_map = dict_encoding_map

    def decode_value(self, encoded_value):
        """
        Decodes a single byte value using the dictionary encoding map.

        :param encoded_value: Byte value to decode.
        :return: Decoded human-readable name, or the byte value if not found in the map.
        """
        return self.dict_encoding_map.get(encoded_value, encoded_value)

    def decode_packet(self, packet):
        """
        Decodes the main variable ID, params, and other fields in the packet.

        :param packet: A dictionary representing the packet data, with fields such as
                       "main_var_id", "value", and "params".
        :return: Decoded packet with human-readable names where possible.
        """
        # Decode the main variable ID
        element_id = self.decode_value(packet.get("element_id"))

        # Decode params, if any
        params = [self.decode_value(param) for param in packet.get("params", [])]

        # Return the decoded packet with human-readable names where possible
        decoded_packet = {
            "element_id": element_id,
            "value": packet.get("value"),
            "params": params,
        }

        return decoded_packet

    def process_raw_data(self, raw_data):
        """
        Processes raw packet data by extracting fields and applying dictionary decoding.

        :param raw_data: Raw data bytes from the serial packet.
        :return: Decoded packet as a dictionary with human-readable names.
        """
        # Here, we'd parse `raw_data` based on the packet structure, e.g.,
        # raw_data should be parsed to extract main_var_id, value, and params.
        # This is a placeholder to show where decoding would occur.

        # Sample parsed data structure from raw_data (mocked for example)
        parsed_packet = {
            "main_var_id": raw_data[0],  # Assuming first byte is main_var_id
            "value": raw_data[1],  # Placeholder for an actual parsed value
            "params": raw_data[2:],  # Placeholder for params extracted from raw_data
        }

        # Decode the parsed data using `decode_packet`
        return self.decode_packet(parsed_packet)
