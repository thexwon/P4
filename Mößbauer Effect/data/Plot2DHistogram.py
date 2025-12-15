#!/usr/bin/env python3

import argparse
from datetime import datetime
import logging
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import os
from scisdk.scisdk import SciSDK
from scisdk.scisdk_defines import *
import tempfile
from time import sleep


# Parse command-line arguments
parser = argparse.ArgumentParser(
    prog="Plot2DHistogram",
    description="Record the data and save it as a 2D NumPy array to a file."
)
parser.add_argument("filename", type=str, help="Name of the file to save the data")  # Filename
# parser.add_argument("--param", type=int, default=5, help="An optional parameter (default=5)")  # Custom integer parameter
parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')  # Verbose debug mode
args = parser.parse_args()


# Create a temporary directory to store the measurement every second in case the program crashes
temp_dir = tempfile.TemporaryDirectory(
    prefix="Plot2DHistogram_",
    dir=tempfile.gettempdir(),
    delete=False
)


# Configure logger
logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)


# Matplotlib RC parameters
plt.rcParams["figure.figsize"] = (15, 7)
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


fig = plt.figure("Energy-Velocity spectrum")
plt.rcParams["figure.figsize"] = (20, 20)

ax1 = fig.add_subplot(1, 1, 1)

# Open connection to the daq device
sdk = SciSDK()

# add new device
script_path = os.path.dirname(os.path.realpath(__file__))  # location of this script
res = sdk.AddNewDevice("usb:60139", "dt1260", f"{script_path}/RegisterFile.json", "board0")

if not res == 0:
    print("Program exit due connection error")
    exit()

# configure firmware register
err = sdk.SetRegister("board0:/Registers/ANALOG_OFFSET", 0)


# print(sdk.GetParameterInteger("board0:/Registers/ANALOG_OFFSET"))
# Set registers
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.trgthrs", 400)
# print(sdk.GetParameterInteger("board0:/MMCComponents/REGFILE_0.trgthrs"))

err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.Nsample", 6)
# print(sdk.GetParameterInteger("board0:/MMCComponents/REGFILE_0.Nsample"))
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.timr_hold_bs", 100)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.Offset_int", 0)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.gain", 500)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.pre_integr", 5)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.time_integr", 76)

err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.trgthrs", 470)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.DELTA", 40)


# set board parameters
sdk.SetParameterString("board0:/MMCComponents/Energy_Channel_Hist.limitmode", "freerun")
sdk.SetParameterString("board0:/MMCComponents/Energy_Channel_Hist.limit", "100")

# execute command reset
sdk.ExecuteCommand("board0:/MMCComponents/Energy_Channel_Hist.reset", "")

# execute command start
sdk.ExecuteCommand("board0:/MMCComponents/Energy_Channel_Hist.start", "")

# measurementTime = 60

# for i in range(measurementTime):
#     print ("Wait " + str(i+1) + "s/{0}s ...".format(measurementTime))
#     sleep(1)

res, buf = sdk.AllocateBuffer("board0:/MMCComponents/Energy_Channel_Hist")

# res, buffer = sdk.ReadData("board0:/MMCComponents/Energy_Channel_Hist", buf)# read data from board

# S = [0 for i in range(buffer.info.binsY)]
# for i in range(buffer.info.binsY):
#     S[i] = [0 for j in range(buffer.info.binsX)]
# if res == 0:
#     for i in range(buffer.info.binsY):
#         for j in range(buffer.info.binsX):
#             S[i][j] = buffer.data[i*buffer.info.binsX+j]
# plt.rcParams["figure.figsize"] = (20,20)
# #plot heatmap
# plt.imshow(S, cmap='jet', interpolation='nearest')
# plt.show()
# help(plt.colorbar)
cbar = None


def GetSpectrum(buffer):
    logging.debug("Connecting to device")
    res, buffer = sdk.ReadData("board0:/MMCComponents/Energy_Channel_Hist", buffer)  # read data from board
    S = [0 for i in range(buffer.info.binsY)]
    for i in range(buffer.info.binsY):
        S[i] = [0 for j in range(buffer.info.binsX)]
    if res == 0:
        logging.debug("Copying data into 2D array")
        for i in range(buffer.info.binsY):
            for j in range(buffer.info.binsX):
                S[i][j] = buffer.data[i * buffer.info.binsX + j]
    else:
        logging.error('Cannot connect successfully to device')
        raise RuntimeError('Failed to read data from device')
    return np.array(S)


# Handler to plot new data on the graph
def updateGraph(i, buffer):
    global cbar
    # update the buffer
    try:
        logging.debug("Fetching new spectrum data")
        S = GetSpectrum(buffer)
    except RuntimeError as e:
        logging.error(f"Error in updateGraph: {e}")
        return

    logging.debug("Clearing the previous axis content")
    plt.clf()
    fig = plt.figure("Energy-Velocity spectrum")
    plt.rcParams["figure.figsize"] = (20, 20)

    ax1 = fig.add_subplot(1, 1, 1)

    # write buffer content to a file
    path_tempfile = f"{temp_dir.name}/{args.filename}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')}.txt"
    np.savetxt(path_tempfile, S, fmt='%d')
    logging.info(f"Saved data to {path_tempfile}")

    logging.debug("Updating the heatmap")
    im = ax1.imshow(S, cmap='jet', interpolation='nearest', origin='lower')
    # Update the axis labels and aspect ratio
    ax1.set_aspect(4)
    ax1.set_xlabel("Velocity")
    ax1.set_ylabel("Energy")

    # print(f"cbar before remove: {cbar}")
    logging.debug("Updating colorbar")
    if cbar is not None:
        # Update the colorbar limits to match the new image data
        cbar.mappable = im
        im.set_clim(np.min(S), np.max(S))  # Update color limits
        cbar.update_ticks()  # Update the ticks
    else:
        # Create the colorbar if it doesn't exist
        cbar = plt.colorbar(im, ax=ax1)
    # Add the new colorbar
    cbar = plt.colorbar(im, ax=ax1)


plt.rcParams["figure.figsize"] = (25, 25)

# update graph continuously
ani = animation.FuncAnimation(fig, updateGraph, fargs=[buf,], interval=1000)
plt.show()


histogram2d = GetSpectrum(buf)
np.savetxt(f"{args.filename}.txt", histogram2d, fmt='%d')

# Clear temporary directory after data was saved successfully to the target file
temp_dir.cleanup()
logging.info("Cleared all temporary files")

sdk.FreeBuffer("board0:/MMCComponents/Energy_Channel_Hist", buf)
