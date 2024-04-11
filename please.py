import serial
import time

# Initialize Serial communication with EmStat Pico
pico_serial = serial.Serial('COM9', 230400, timeout=1)

print("Starting CV Measurement...")

# Send the command to enter MethodSCRIPT mode
# Wait a bit for the command to be processed
time.sleep(0.1)

lsv = [
    "e",
    "var c",
    "var p",
    "set_pgstat_chan 1",
    "set_pgstat_mode 0",
    "set_pgstat_chan 0",
    "set_pgstat_mode 2",
    "set_max_bandwidth 40",
    "set_range_minmax da -500m 800m",
    "set_range ba 9218750p",
    "set_autoranging ba 9218750p 2950u",
    "set_e 0",
    "cell_on",
    "meas_loop_ca p c 0 500m 2",
    "pck_start",
    "pck_add p",
    "pck_add c",
    "pck_end",
    "endloop",
    "meas_loop_cv p c 0 -500m 800m 10m 100m nscans(2)",
    "pck_start",
    "pck_add p",
    "pck_add c",
    "pck_end",
    "endloop",
    "on_finished:",
    "cell_off",
    "",
]

for command in lsv:
    pico_serial.write((command + '\n').encode())
    time.sleep(0.1)  # Wait a bit after sending each command to ensure it's processed

# Main loop to handle incoming data from EmStat Pico
while True:
    if pico_serial.in_waiting > 0:
        incoming_data = pico_serial.readline().decode().strip()
        print(incoming_data)
