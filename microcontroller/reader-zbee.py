'''
This script reads microcontroller output on serial port 
Expected data format is bytestring of individual sensor values seperated by whitespaces. Each datapoint is seperated by a newline (\n) and return carriage (\r) . Ex. (for n data points) input will be: 

b'D1 D2 D3 ... Dn\n\r'

For each sensor Di

Each datapoint is output by this script in the form of a list of strings:

[TIMESTAMP D1 D2 D3 ... Dn]

Configuration of of n is done on the microcontroller. This script should work as expected regardless of how many sensors are actually connected to the microcontroller

ERR* indicates errors; Error numbers denote the following:

ERR1: Chip stuck in command mode
ERR2: Stale data (data has been already recieved)
ERR3: Sensor diagnostic fault
ERR4: Sensor missing (check the PCB if sensor is expected to be in place)

'''

'''

TODO Add reset condition if 3 or more timeouts detected
TODO Find the reason for periodic timeouts - for some reason communication seems to stop and the port needs to be restarted in order for it to work
 - This seems to be related with the number of devices the microcontroller is serving
TODO Inspect why error numbers ERR* seem to periodically disappear (itoa problem?)
DONE Add timestamps to data
DONE if ACM0 does no exist, catch that exception and try other ttyACM*
DONE ignore all recieved data for the first 2 seconds
'''

import serial
import time
import sys
from digi.xbee.devices import XBeeDevice
from digi.xbee.io import IOLine, IOMode

# device = serial.Serial('/dev/ttyACM0', 9600, timeout=2);

def connect():
    connected = False
    curr_dev = 0 # ttyACM* dev number
    dev_addr = "/dev/ttyACM"
    curr_dev_addr = ""
    while not connected:
        curr_dev_addr = dev_addr + str(curr_dev)
        try:
            device = serial.Serial(curr_dev_addr, 9600, timeout=2)
            connected = True
        except (serial.SerialException, FileNotFoundError) as e:
            curr_dev += 1
            curr_dev %= 10
    return device

def initData(device):
    epoch = time.time()
    curr_time = time.time()
    while curr_time - epoch <= 2:
        getData(device)
        curr_time = time.time()
        
def getData(device):
    vals = []
    try:
        curr_time = time.time()
        line = device.readline()
        vals = line.decode('utf-8').rsplit()
        curr_time = str(curr_time)
        curr_time = curr_time[:curr_time.find('.')+3] # truncate to 2 decimal points
        vals.insert(0, curr_time)
        return vals;
    except (serial.SerialTimeoutException, UnicodeDecodeError):
        return vals

def handleTimeout(device):
    print("TIMEOUT") #this should perhaps be logged
    device.close()
    device.open()
    return device

def printData(values):
    output = ""
    try:
        for value in values:
            output += value
            output += " "
        print(output)
    except IndexError:
        pass
        
def main():
    device = connect()
    initData(device)
    zigbee_device = XBeeDevice('', 115200)
    REMOTE_NODE_ID = "Main"
    xbee_network = zigbee_device.get_network()
    remote_device = xbee_network.discover_device(REMOTE_NODE_ID)
    
    while True:
        values = getData(device)
        if len(values) <= 1: # only got the currtime
            device = handleTimeout(device)
        else:
            # do something with data (printing for now)
            # printData(values)
            zigbee_device.send_data(remote_device, values[2]) 

# Don't stop even if device gets disconnected            
while True:
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting.. \n")
        sys.exit()
    except serial.SerialException:
        continue
    except:
        continue
