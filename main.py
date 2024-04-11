import serial
from time import sleep
import pandas as pd
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106

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
serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

# Send the command to enter MethodSCRIPT mode

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

with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((10, 10), "Starting Test", fill="white")

for command in cv:
    pico_serial.write((command + '\n').encode())
    sleep(0.1)  # Wait a bit after sending each command to ensure it's processed

with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((10, 10), "Test in progress", fill="white")
    draw.text((20, 10), "0%", fill="blue")

df = pd.DataFrame(columns=["Potential", "Current"])
ca_done = False
test_progress, test_size = 0, 300

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
        else:
            test_progress += 1
            if test_progress % 10 == 0:
                with canvas(device) as draw:
                    draw.rectangle(device.bounding_box, outline="white", fill="black")
                    draw.text((10, 10), "Test in progress", fill="white")
                    draw.text((20, 10), f"{test_progress/test_size*100}%", fill="blue")

        parsed_data = parse_data(incoming_data)
        if(parsed_data):
            df = df._append({"Potential": parsed_data[0], "Current": parsed_data[1]}, ignore_index=True)

with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((10, 10), "Analyzing test results", fill="white")
    draw.text((20, 10), "0%", fill="blue")

# Load baseline as a dataframe from baseline.csv
baseline = pd.read_csv("baseline.csv")

test_result = False
# Iterate over the dataframe and compare the current values to the baseline looking for peaks in difference
for i, row in df.iterrows():
    # Find the two voltages that our's falls between
    lower_voltage = baseline.loc[baseline['Potential'] <= row['Potential']].iloc[-1]
    upper_voltage = baseline.loc[baseline['Potential'] >= row['Potential']].iloc[0]

    # Interpolate the current values
    interpolated_current = lower_voltage['Current'] + (upper_voltage['Current'] - lower_voltage['Current']) * (row['Potential'] - lower_voltage['Potential']) / (upper_voltage['Potential'] - lower_voltage['Potential'])

    # Compare the interpolated current to the measured current and if the difference is greater than 1.5 microamps print it
    if abs(interpolated_current - row['Current']) > 1.5:
        test_result = True
        break

    # Update the progress bar
    if i % 10 == 0:
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((10, 10), "Analyzing test results", fill="white")
            draw.text((20, 10), f"{i/len(df)*100}%", fill="blue")

test_result_output = "Positive +" if test_result else "Negative -"

with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((10, 10), test_result, fill="white")

sleep(5)