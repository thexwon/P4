from random import randint
from unicodedata import decimal
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import os
from scisdk.scisdk import SciSDK
from scisdk.scisdk_defines import *
import argparse

# Function to parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Plot signal data from the gamma detector")
    # Add positional argument for the filename
    # parser.add_argument("filename", type=str, help="Name of the file to save the data")
    
    # Add an optional argument for a custom integer parameter
    parser.add_argument("--scaleTime", type=int, default=1000, help="Scaling of the time (default=1000)")
    
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




fig = plt.figure("Oscilloscope analog data - channel 0")
ax1 = fig.add_subplot(1,1,1)

# initialize scisdk library
sdk = SciSDK()
# add new device

#DT1260
script_path = os.path.dirname(os.path.realpath(__file__))
res = sdk.AddNewDevice("usb:60139", "dt1260", script_path +
                       "/RegisterFile.json", "board0")
#DT5560
#res = sdk.AddNewDevice("192.168.50.10:8888","DT5560", "./DT5560RegisterFile.json","board0")
#DT5550
#res = sdk.AddNewDevice("usb:11000","DT5550", "./DT5550RegisterFile.json","board0")
#V2740
#res = sdk.AddNewDevice("192.168.50.10","V2740", "./V2740RegisterFile.json","board0")


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


err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.trgthrs",420)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.DELTA",40)



# set oscilloscope parameters
res = sdk.SetParameterString("board0:/MMCComponents/Oscilloscope_0.data_processing","decode")
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_0.trigger_level", 3000)
res = sdk.SetParameterString("board0:/MMCComponents/Oscilloscope_0.trigger_mode","self")
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_0.trigger_channel", 0)
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_0.pretrigger", 150)
decimator = args.scaleTime
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_0.decimator", decimator)
res = sdk.SetParameterString("board0:/MMCComponents/Oscilloscope_0.acq_mode", "blocking")
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_0.timeout", 3000)
# allocate buffer for oscilloscope
res, buf = sdk.AllocateBuffer("board0:/MMCComponents/Oscilloscope_0")


def updateGraph(i, buffer, decimator): # function that provides to plot new data on graph
    res, buffer = sdk.ReadData("board0:/MMCComponents/Oscilloscope_0", buffer)# read data from board
    if res == 0:
        xar = []
        yar = []
        for index in range(buffer.info.samples_analog):
            xar.append(index * decimator)
            yar.append(buffer.analog[index])
        global pause
        if not pause:
            ax1.clear()
            ax1.plot(xar,yar)
            ax1.axhline(y=np.mean(yar),lw=3,c='r',ls=':')
            ax1.set_ylim(0,4000)
            ax1.set_xlabel('Time')
            ax1.set_ylabel('Signal')


pause = False
def onClick(event):
    global pause
    pause = not pause

fig.canvas.mpl_connect('button_press_event', onClick)
# update graph every 50ms
ani = animation.FuncAnimation(fig, updateGraph, fargs=[buf, decimator,],interval=1)
# updateGraph(None, buf, decimator)
plt.show()

print('Finished')