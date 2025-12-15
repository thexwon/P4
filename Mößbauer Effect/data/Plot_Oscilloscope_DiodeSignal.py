from random import randint
from unicodedata import decimal
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import os
from scisdk.scisdk import SciSDK
from scisdk.scisdk_defines import *

plt.rcParams["figure.figsize"] = (25,20)
plt.rcParams['xtick.labelsize'] = 20 
plt.rcParams['ytick.labelsize'] = 20
plt.rcParams['axes.grid'] = True 
plt.rcParams['legend.fontsize'] = 22
plt.rcParams['axes.labelsize'] = 20
plt.rcParams['figure.titlesize'] = 22
plt.rcParams['axes.formatter.useoffset'] = False
# plt.rcParams.keys()
# %config InlineBackend.print_figure_kwargs={'facecolor' : "w"}
plt.rcParams['figure.facecolor'] = 'white'  # Set default figure background
plt.rcParams['axes.facecolor'] = 'white'  # Set default axes background



fig = plt.figure("Oscilloscope data")
ax5 = fig.add_subplot(5,1,5)
ax1 = fig.add_subplot(5,1,1, sharex=ax5)
ax2 = fig.add_subplot(5,1,2, sharex=ax5)
ax3 = fig.add_subplot(5,1,3, sharex=ax5)
ax4 = fig.add_subplot(5,1,4, sharex=ax5)

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


err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.trgthrs",470)
err = sdk.SetParameterInteger("board0:/MMCComponents/REGFILE_1.DELTA",45)



# set oscilloscope parameters
res = sdk.SetParameterString("board0:/MMCComponents/Oscilloscope_1.data_processing","decode")
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_1.trigger_level", 3000)
res = sdk.SetParameterString("board0:/MMCComponents/Oscilloscope_1.trigger_mode","self")
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_1.trigger_channel", 0)
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_1.pretrigger", 150)
decimator = 100
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_1.decimator", decimator)
res = sdk.SetParameterString("board0:/MMCComponents/Oscilloscope_1.acq_mode", "blocking")
res = sdk.SetParameterInteger("board0:/MMCComponents/Oscilloscope_1.timeout", 1000)
# allocate buffer for oscilloscope
res, buf = sdk.AllocateBuffer("board0:/MMCComponents/Oscilloscope_1")

# print(buf.info.tracks_digital_per_channel)
# help(buf.info)
# exit(0)



def updateGraph(i, buffer, decimator): # function that provides to plot new data on graph
    res, buffer = sdk.ReadData("board0:/MMCComponents/Oscilloscope_1", buffer)# read data from board
    if res == 0:
        xar = []
        yar = []
        for index in range(buffer.info.samples_analog):
            xar.append(index * decimator)
            yar.append(buffer.analog[index])
        xar2 = []
        yar2 = []
        for index in range(buffer.info.samples_analog):
            xar2.append(index * decimator)
            yar2.append(buffer.analog[index + 2 * buf.info.samples_analog])
        xarDig = []
        yarDig = []
        for index in range(buffer.info.samples_digital):
            xarDig.append(index * decimator)
            yarDig.append(buffer.digital[index])
        xarDig3 = []
        yarDig3 = []
        for index in range(buffer.info.samples_digital):
            xarDig3.append(index * decimator)
            yarDig3.append(buffer.digital[index+4*buf.info.samples_digital])
        xarDig5 = []
        yarDig5 = []
        for index in range(buffer.info.samples_digital):
            xarDig5.append(index * decimator)
            yarDig5.append(buffer.digital[index+12*buf.info.samples_digital])
        global pause
        if not pause:
            ax1.clear()
            ax1.plot(xar,yar)
            ax1.axhline(y=np.mean(yar),lw=3,c='r',ls=':')
            ax1.set_ylabel('Signal')
            
            ax2.clear()
            ax2.plot(xarDig,yarDig)
            ax2.set_ylabel('Next \n channel')
                   
            ax3.clear()
            ax3.plot(xar2,yar2)
            ax3.set_ylim(0,1048)
            ax3.set_ylabel('Current \n channel')

            ax4.clear()
            ax4.plot(xarDig3,yarDig3)
            ax4.set_ylabel('Start \n signal')

            ax5.clear()
            ax5.plot(xarDig5,yarDig5)
            ax5.get_xaxis().tick_bottom()
            ax4.set_xticks([])
            ax5.set_xlabel('Time')
            ax5.set_ylabel('Max-Min \n switch')
plt.subplots_adjust(hspace=0.5)

pause = False
def onClick(event):
    global pause
    pause = not pause

fig.canvas.mpl_connect('button_press_event', onClick)
# update graph every 50ms
ani = animation.FuncAnimation(fig, updateGraph, fargs=[buf, decimator,],interval=100)
# updateGraph(None, buf, decimator)
plt.show()