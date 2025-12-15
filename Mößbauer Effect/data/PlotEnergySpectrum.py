from time import sleep
import os
from scisdk.scisdk import SciSDK
from scisdk.scisdk_defines import *
from unicodedata import decimal
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import numpy as np
from datetime import datetime

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


fig = plt.figure("Energy spectrum")
ax1 = fig.add_subplot(1,1,1)


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
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.trgthrs",400)
# print(sdk.GetParameterInteger("board0:/MMCComponents/REGFILE_0.trgthrs"))

err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.Nsample",6)
# print(sdk.GetParameterInteger("board0:/MMCComponents/REGFILE_0.Nsample"))
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.timr_hold_bs",100)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.Offset_int",0)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.gain",500)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.pre_integr",5)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_0.time_integr",76)


err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.trgthrs",420)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.DELTA",40)


# set board parameters
sdk.SetParameterString("board0:/MMCComponents/Spectrum_0.rebin", "0")
sdk.SetParameterString("board0:/MMCComponents/Spectrum_0.limitmode", "freerun")
sdk.SetParameterString("board0:/MMCComponents/Spectrum_0.limit", "100")

# execute command reset
sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_0.reset", "")

# execute command start
sdk.ExecuteCommand("board0:/MMCComponents/Spectrum_0.start", "")

# measurementTime = 20

# for i in range(measurementTime):
#     print ("Wait " + str(i+1) + "s/{0}s ...".format(measurementTime))
#     sleep(1)

# # allocate buffer
# res, buf = sdk.AllocateBuffer("board0:/MMCComponents/Spectrum_0")

# if res == 0:
#     # read data
#     res, buf = sdk.ReadData("board0:/MMCComponents/Spectrum_0", buf)

#     if res == 0:
#         str_tmp = ""
#         for i in range(buf.info.total_bins):
#             str_tmp += str(buf.data[i]) + "\n"

#         # write data into a file
#         file = open("energy_spectrum_test.txt", "w")
#         file.write(str_tmp)
#         file.close()
#     else:
#         # print error description
#         res, err = sdk.s_error(res)
#         print("Read data error:", err)

#     sdk.FreeBuffer("board0:/MMCComponents/Spectrum_0", buf)

# else:
#     # print error description
#     res, err = sdk.s_error(res)
#     print("Allocate buffer error:", err)

# allocate buffer
res, buf = sdk.AllocateBuffer("board0:/MMCComponents/Spectrum_0")

def updateGraph(i, buffer): # function that provides to plot new data on graph
    res, buffer = sdk.ReadData("board0:/MMCComponents/Spectrum_0", buffer)# read data from board
    if res == 0:
        xar = []
        yar = []
        for index in range(buffer.info.total_bins):
            xar.append(index)
            yar.append(buffer.data[index])
        ax1.clear()
        ax1.plot(xar,yar)
        ax1.set_xlabel('ADC channel')
        ax1.set_ylabel('Counts')

# update graph every 50ms
ani = animation.FuncAnimation(fig, updateGraph, fargs=[buf,],interval=100)
# updateGraph(None, buf, decimator)
plt.show()

def GetSpectrum(buffer):
    res, buffer = sdk.ReadData("board0:/MMCComponents/Spectrum_0", buffer)# read data from board
    if res == 0:
        xar = []
        yar = []
        for index in range(buffer.info.total_bins):
            xar.append(index)
            yar.append(buffer.data[index])
    else:
        print('Something went wrong')
    return xar, yar
x, y = GetSpectrum(buf)
np.savetxt("EnergySpectrum_{0}.txt".format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S")), np.vstack((x,y)).T,fmt='%d')