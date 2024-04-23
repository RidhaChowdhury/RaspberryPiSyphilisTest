import serial
from time import sleep
import pandas as pd
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
import gpiod as io
from test_lib import *

# Button connection
chip = io.Chip("gpiochip4")
button = chip.get_line(23)
button.request(consumer="button", type=io.LINE_REQ_EV_BOTH_EDGES)

# Initialize Serial communication with Sensit
pico_serial = serial.Serial('/dev/ttyUSB0', 230400, timeout=1)
serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

try:
    while True:
        # Waiting for test to be triggered
        while button.get_value() == 0:
            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, outline="black", fill="black")
                draw.text((0, 10), "Flip Switch to", fill="white")
                draw.text((10, 30), "Start Test", fill="white")
            sleep(0.1)
        
        # Start test loop
        while button.get_value() == 1:

            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, outline="black", fill="black")
                draw.text((10, 10), "Starting Test", fill="white")

            for command in cv:
                pico_serial.write((command + '\n').encode())
                sleep(0.1)  # Wait a bit after sending each command to ensure it's processed

            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, outline="black", fill="black")
                draw.text((10, 10), "Test in progress", fill="white")
                draw.text((40, 50), "0%", fill="blue")

            df = pd.DataFrame(columns=["Potential (V)", "Current (A)"])
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
                                draw.rectangle(device.bounding_box, outline="black", fill="black")
                                draw.text((10, 10), "Test in progress", fill="white")
                                draw.text((40, 50), f"{round(test_progress/test_size*100, 4)}%", fill="blue")

                    parsed_data = parse_data(incoming_data)
                    if(parsed_data):
                        df = df._append({"Potential (V)": parsed_data[0], "Current (A)": parsed_data[1]}, ignore_index=True)

            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, outline="black", fill="black")
                draw.text((10, 10), "Analyzing test results", fill="white")
                draw.text((40, 50), "0%", fill="blue")

            # Load baseline as a dataframe from baseline.csv
            baseline = pd.read_csv("baseline.csv")

            test_result = False
            # Iterate over the dataframe and compare the current values to the baseline looking for peaks in difference
            for i, row in df.iterrows():
                # Find the two voltages that our's falls between
                lower_voltage = baseline.loc[baseline['Potential (V)'] <= row['Potential (V)']].iloc[-1]
                upper_voltage = baseline.loc[baseline['Potential (V)'] >= row['Potential (V)']].iloc[0]

                # Interpolate the current values
                interpolated_current = lower_voltage['Current (A)'] + (upper_voltage['Current (A)'] - lower_voltage['Current (A)']) * (row['Potential (V)'] - lower_voltage['Potential (V)']) / (upper_voltage['Potential (V)'] - lower_voltage['Potential (V)'])

                # Compare the interpolated current to the measured current and if the difference is greater than 1.5 microamps print it
                if abs(interpolated_current - row['Current (A)']) > 1.5:
                    test_result = True
                    break

                # Update the progress bar
                if i % 10 == 0:
                    with canvas(device) as draw:
                        draw.rectangle(device.bounding_box, outline="black", fill="black")
                        draw.text((10, 10), "Analyzing test results", fill="white")
                        draw.text((40, 50), f"{round(i/len(df)*100, 4)}%", fill="blue")

            test_result_output = "Positive +" if test_result else "Negative -"

            with canvas(device) as draw:
                draw.rectangle(device.bounding_box, outline="black", fill="black")
                draw.text((30, 10), test_result, fill="white")
            
            sleep(3)

            # Starting new test in countdown
            for i in range(5, 0, -1):
                with canvas(device) as draw:
                    draw.rectangle(device.bounding_box, outline="black", fill="black")
                    draw.text((30, 10), test_result, fill="white")
                    draw.text((10, 10), "Starting New Test in", fill="white")
                    draw.text((40, 30), f"{i}", fill="blue")

                if button.get_value() == 0:
                    break
                
                sleep(1)




finally:
    button.release()
    chip.close()