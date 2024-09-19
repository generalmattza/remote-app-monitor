import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")

import math


def gen_sine(amplitude=1, frequency=1, offset=0, phase=0, decimals=2):
    while True:
        yield round(
            amplitude * math.sin(2 * math.pi * frequency * time.time() + phase)
            + offset,
            decimals,
        )


progress = gen_sine(amplitude=50, frequency=0.1, offset=50)
processed = iter(range(1000))

while True:
    var = next(progress)
    socket.send_string(f"progress_1 {var}")
    print(f"progress_1={var}")
    socket.send_string(f"table_1 Processed 1m {next(processed)}")
    time.sleep(1 / 120)
