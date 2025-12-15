from time import sleep
import os
from scisdk.scisdk import SciSDK
from scisdk.scisdk_defines import *
from unicodedata import decimal
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import time
from datetime import datetime
import numpy as np
import argparse

# Function to parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Record velocity calibration data and save it as a 1D NumPy array to a file.")
    # Add positional argument for the filename
    # parser.add_argument("filename", type=str, help="Name of the file to save the data")
    
    # Add an optional argument for a custom integer parameter
    parser.add_argument("--time", type=int, default=10, help="Measurement time (default=10)")
    
    return parser.parse_args()

args = parse_args()


plt.rcParams["figure.figsize"] = (15,7)
plt.rcParams['xtick.labelsize'] = 22 
plt.rcParams['ytick.labelsize'] = 22
plt.rcParams['axes.grid'] = True 
plt.rcParams['legend.fontsize'] = 22
plt.rcParams['axes.labelsize'] = 25
plt.rcParams['figure.titlesize'] = 22
plt.rcParams['axes.formatter.useoffset'] = False
# plt.rcParams.keys()
# %config InlineBackend.print_figure_kwargs={'facecolor' : "w"}
plt.rcParams['figure.facecolor'] = 'white'  # Set default figure background
plt.rcParams['axes.facecolor'] = 'white'  # Set default axes background

fig = plt.figure("Velocity calibration spectrum")
ax1 = fig.add_subplot(1,1,1)
# ax2 = fig.add_subplot(2,1,2)



sdk = SciSDK()
# add new device
script_path = os.path.dirname(os.path.realpath(__file__))
res = sdk.AddNewDevice("usb:60139", "dt1260", script_path +
                       "/RegisterFile.json", "board0")

if not res == 0:
    print("Program exit due connection error")
    exit()

# configure firmware register
err = sdk.SetRegister("board0:/Registers/ANALOG_OFFSET", 0)


# print(sdk.GetParameterInteger("board0:/Registers/ANALOG_OFFSET"))
# Set registers
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.trgthrs",300)
# print(sdk.GetParameterInteger("board0:/MMCComponents/REGFILE_0.trgthrs"))

err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.Nsample",6)
# print(sdk.GetParameterInteger("board0:/MMCComponents/REGFILE_0.Nsample"))
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.timr_hold_bs",100)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.Offset_int",0)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.gain",300)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.pre_integr",5)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.time_integr",76)


err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.trgthrs",470)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.DELTA",45)


# set board parameters
sdk.SetParameterString("board0:/MMCComponents/Spectrum_calibration.rebin", "0")
sdk.SetParameterString("board0:/MMCComponents/Spectrum_calibration.limitmode", "freerun")
sdk.SetParameterString("board0:/MMCComponents/Spectrum_calibration.limit", "100")

# execute command reset
sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_calibration.reset", "")

# execute command start
sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_calibration.start", "")



# allocate buffer
res, buf = sdk.AllocateBuffer("board0:/MMCComponents/Spectrum_calibration")

def updateGraph(i, buffer): # function that provides to plot new data on graph
    global clear
    if clear:
        # execute command stop
        sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_calibration.stop", "")
        # execute command reset
        sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_calibration.reset", "")
        # execute command start
        sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_calibration.start", "")
        clear = False

    res, buffer = sdk.ReadData("board0:/MMCComponents/Spectrum_calibration", buffer)# read data from board
    if res == 0:
        xar = []
        yar = []
        for index in range(buffer.info.total_bins):
            xar.append(index)
            yar.append(buffer.data[index])
        ax1.clear()
        ax1.plot(xar,yar)
        ax1.set_xlabel('Velocity channel')
        ax1.set_ylabel('Counts')

clear = False
def onClick(event):
    global clear
    clear = True

fig.canvas.mpl_connect('button_press_event', onClick)

# update graph every 50ms
ani = animation.FuncAnimation(fig, updateGraph, fargs=[buf,],interval=100)
# updateGraph(None, buf, decimator)
plt.show()


# execute command reset
sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_calibration.reset", "")

# execute command start
sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_calibration.start", "")


measurementTime = args.time

for i in range(measurementTime):
    print ("Wait " + str(i+1) + "s/{0}s ...".format(measurementTime))
    sleep(1)

# execute command stop
sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_calibration.stop", "")

# allocate buffer
res, buf = sdk.AllocateBuffer("board0:/MMCComponents/Spectrum_calibration")

if res == 0:
    # read data
    res, buf = sdk.ReadData("board0:/MMCComponents/Spectrum_calibration", buf)

    if res == 0:
        str_tmp = ""
        for i in range(buf.info.total_bins):
            str_tmp += str(buf.data[i]) + "\n"

        # write data into a file
        file = open("VelocityCalibration_{0}_{1}_seconds.txt".format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),\
                                                             args.time), "w")
        file.write(str_tmp)
        file.close()
    else:
        # print error description
        res, err = sdk.s_error(res)
        print("Read data error:", err)

    sdk.FreeBuffer("board0:/MMCComponents/Spectrum_calibration", buf)

else:
    # print error description
    res, err = sdk.s_error(res)
    print("Allocate buffer error:", err)