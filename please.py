import serial
import time
import pandas as pd

def parse_data(data):
    data = data.split(';')

    # Data comes back in the following structure:'Pda801B69Bu; ba842C1C4f,14,204
    # Where the first part 801B69Bu is the potential in hex form with the u denoting microvolts
    # and the second part 842C1C4f is the current in hex form with the f denoting femtoamps
    # filter out returns that have other unit characters
    
    # Parse the potential and current
    if data[0][-1] != 'u' or data[1][data[1].index(',') - 1] != 'f':
        return None

    potential = int(data[0][3:-1], 16)
    current = int(data[1][3:data[1].index(',') - 1], 16)

    return potential, current

# Initialize Serial communication with EmStat Pico
pico_serial = serial.Serial('/dev/ttyUSB0', 230400, timeout=1)

# Send the command to enter MethodSCRIPT mode
# Wait a bit for the command to be processed
time.sleep(0.1)

cv = [
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
    "meas_loop_cv p c 0 -500m 800m 10m 100m nscans(1)",
    "pck_start",
    "pck_add p",
    "pck_add c",
    "pck_end",
    "endloop",
    "on_finished:",
    "cell_off",
    "",
]
df = pd.DataFrame(columns=["Potential", "Current"])

for command in cv:
    pico_serial.write((command + '\n').encode())
    time.sleep(0.1)  # Wait a bit after sending each command to ensure it's processed

ca_done = False
# Main loop to handle incoming data from EmStat Pico
while True:
    if pico_serial.in_waiting > 0:
        incoming_data = pico_serial.readline().decode().strip()
        if(incoming_data == "*" ):
            if(ca_done):
                break
            ca_done = True

        if(len(incoming_data) == 0 or incoming_data[0] != 'P' or not ca_done):
            continue

        parsed_data = parse_data(incoming_data)
        if(parsed_data):
            df = df._append({"Potential": parsed_data[0], "Current": parsed_data[1]}, ignore_index=True)


# Print the dataframe
print(df)