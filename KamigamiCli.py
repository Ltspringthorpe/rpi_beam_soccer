from __future__ import print_function
import argparse
import time
from bluepy import btle
from bluepy.btle import Scanner, DefaultDelegate
import os
import signal
from random import choice
import codecs


"""
!! Note !!

The first few hundred lines of this file are just KamigamiData.py (with a few
modifications).  They have been copied in to make an all 
inclusive, easy-to-run, cli.

!! Note !!
"""

class KamigamiRobot:
    """
    Class that contains information specific to the Kamigami Robot
    """
    MAIN_SERVICE_UUID = '708a96f0f2004e2f96f09bc43c3a31c8'
    WRITE_UUID  = '708a96f1f2004e2f96f09bc43c3a31c8'
    NOTIFY_UUID = '708a96f2f2004e2f96f09bc43c3a31C8'

    class Identifiers:
        LIGHT_PACKET = 2
        MOTOR_PACKET = 3
        IR_PACKET = 5
        TEST_MODE = 16
        STICKY_PACKET_SET = 12
        UNIFIED_PACKET = 15
        SHUTDOWN = 1

    class Settings:
        IMU_NOTIFY_PER_SECOND = 20
        LUX_NOTIFY_PER_SECOND = 10
        MOTOR_SETTINGS_NOTIFY_PER_SECOND = 0


class KamigamiByteFormatter:
    """
    Formats packets for outgoing data to the Kamigami Robot.
    """

    # Get a motor packet to send to the robot.
    @staticmethod
    def get_sendable_motor_packet(left, right):
        if left >= 64 or left <= -64:
            raise ValueError("Please specify a left speed correctly.  Speeds must be between -63 and 63, inclusive.")
        if right >= 64 or right <= -64:
            raise ValueError("Please specify a right speed correctly.  Speeds must be between -63 and 63, inclusive.")
        return KamigamiByteFormatter.convert_params_to_message([KamigamiRobot.Identifiers.MOTOR_PACKET, left, right])

    # Get a light packet to send to the robot
    @staticmethod
    def get_sendable_light_packet(color=None, r=None, g=None, b=None):
        print(r,g,b)
        if color is not None and (r is not None or g is not None or b is not None):
            raise ValueError("Choose a color or specifying r, g, b values")
        if r is not None and g is not None and b is not None:
            if 0 > r or 255 < r:
                raise ValueError("Please specify a red color value correctly.  Color must be between 0 and 255, inclusive.")
            if 0 > g or 255 < g:
                raise ValueError("Please specify a green color value correctly.  Color must be between 0 and 255, inclusive.")
            if 0 > b or 255 < b:
                raise ValueError("Please specify a blue color value correctly.  Color must be between 0 and 255, inclusive.")
            data_ = KamigamiByteFormatter.convert_params_to_message([KamigamiRobot.Identifiers.LIGHT_PACKET, r, g, b])
            return data_
        if color.lower() == "red":
            # return "02ff0000".decode('hex')
            return KamigamiByteFormatter.get_sendable_light_packet(r=255, g=0, b=0)
        elif color.lower() == "blue":
            # return "020000ff".decode('hex')
            return KamigamiByteFormatter.get_sendable_light_packet(r=0, g=0, b=255)
        elif color.lower() == "green":
            # return "0200ff00".decode('hex')
            return KamigamiByteFormatter.get_sendable_light_packet(r=0, g=255, b=0)
        elif color.lower() == "yellow":
            return KamigamiByteFormatter.get_sendable_light_packet(r=255, g=255, b=0)
        elif color.lower() == "purple":
            return KamigamiByteFormatter.get_sendable_light_packet(r=127, g=0, b=127)
        elif color.lower() == "cyan":
            return KamigamiByteFormatter.get_sendable_light_packet(r=0, g=255, b=255)
        else:
            raise ValueError("Bad Arguments")

    @staticmethod
    def get_sendable_ir_packet():
        choice_values = ['\x08\x02', '\x07\x02', '\x06\x02']
        return KamigamiByteFormatter.convert_to_byte(KamigamiRobot.Identifiers.IR_PACKET) + choice(choice_values)

    @staticmethod
    def get_sendable_shutdown():
        return KamigamiByteFormatter.convert_to_byte(KamigamiRobot.Identifiers.SHUTDOWN)

    @staticmethod
    def get_sendable_testmode(speed):
        """
        Puts the robot in "Robot Test Mode,"
        which will test the lights and motors.
        Motor speed is the parameter.
        """
        return KamigamiByteFormatter.convert_params_to_message([KamigamiRobot.Identifiers.TEST_MODE, 1, speed, speed])

    @staticmethod
    def convert_to_byte(value):
        """
        Method used to format integers into
        bytes for the robot to interpret.
        """
        # Negative number
        if str(value)[0] == "-":
            bytes_val = codecs.decode(hex(256+int(value))[2:], 'hex_codec')
            return str(bytes_val)
            # return hex(256+int(value))[2:].decode('hex')
        # Single digit hex value (positive)
        if len(hex(value)) == 3:
            bytes_val = codecs.decode("0"+hex(value)[2:], 'hex_codec')
            return str(bytes_val)
            # return ("0"+hex(value)[2:]).decode('hex')
        else:
            # Double digit hex value
            bytes_val = codecs.decode(hex(value)[2:], 'hex_codec')
            return str(bytes_val)
            # return hex(value)[2:].decode('hex')

    @staticmethod
    def convert_params_to_message(values):
        """
        For each index in the list parameter, convert it to 
        bytes that the robot can interpret.  Then, join
        the command together.
        """
        return "".join(map(KamigamiByteFormatter.convert_to_byte, values))

    @staticmethod
    def get_unified_packet(motor_power=None, lights=None):
        """
        Arguments as follows:

        motor_power: Two element list or tuple containing the left speed
                     in index 0 and right speed in index 1.

        lights: Three element list or tuple containing r,g,b in positions
                0, 1, and 2 respectively.

        """
        cmd = [KamigamiRobot.Identifiers.UNIFIED_PACKET] + [0x0 for i in range(19)] # Set all positions to 0x0
        if motor_power is not None:
            if not all(map(lambda speed: 0 <= speed <= 63, motor_power)):
                raise AttributeError("Motor parameters out of 0 to 63 (inclusive) range.")
            cmd[1] |= 0x01
            cmd[2] = motor_power[0]
            cmd[3] = motor_power[1]
        if lights is not None:
            if not all(map(lambda color: 0 <= color <= 255, lights)):
                raise AttributeError("Specified light values are out of range.")
            cmd[1] |= 0x04
            cmd[6] = lights[0]
            cmd[7] = lights[1]
            cmd[8] = lights[2]

        return KamigamiByteFormatter.convert_params_to_message(cmd)

class AdaptedWriter():
	"""
	The bluepy write method is different then the Adafruit
	write method.  This method will "normalize" them, so that
	a KamigamiInterface file is roughly compatible with Linux and
	Mac.
	"""
	def __init__(self, writer):
		self.writer = writer

	def write_value(self, message):
		self.writer.write(message)

# def cli_input():
#    print(">>> ", end="")
#    return input()

def receive_data(data):
    do_cli(AdaptedWriter(writer), data.split())
    
def do_cli(writer, user_input):
    if user_input[0] == "help":
        print("Help:")
        print("""
    rawnum: Send data in raw numbers.  Seperate each different number with a space.
            Ex: "rawnum 3 63 63" will turn the motors to full forward.
    rawhex: Send data specified in hex values.  Seperate different values with a space.
            Ex: "rawhex 0x0 0x3f 0x3f" will turn the motors to full forward.
    motors: Set the motors to a specific speed.  Command is formatted as motors <left-speed> <right-speed>.
            Ex: "motors 10 10" will set the speed of both motors to 10.
    lights: Sets the lights to a specified color.  Command is formatted as lights <r> <g> <b>.  
            Ex: "lights 255 0 0" will set the lights to red.
    ir:     Sends an IR packet.
    shutdown: Shuts the robot down.
    testmode: Puts the robot in testmode.  Command is formatted as testmode <speed of both motors>.
              Ex: testmode 10 will put the robot in testmode, and the motors will spin with speed 10.
    exit:   Exits the CLI.    

              """)
    elif user_input[0] == "rawnum":
        writer.write_value(KamigamiByteFormatter.convert_params_to_message([int(i) for i in user_input[1:]]))
    elif user_input[0] == "rawhex":
        if all([str(i)[:2] == "0x" for i in user_input[1:]]):
            writer.write_value(KamigamiByteFormatter.convert_params_to_message([int(i[2:], 16) for i in user_input[1:]]))
        else:
            print("Malformatted hex codes.")
    elif user_input[0] == "motors":
        # Without two arguments, break out
        if len(user_input[1:]) < 2:
            print("Please specify a left and right motor speed.")
            return
        writer.write_value(KamigamiByteFormatter.get_sendable_motor_packet(int(user_input[1]), int(user_input[2])))
    elif user_input[0] == "lights":
        # Without three arguments, break out
        if len(user_input[1:]) < 3:
            print("Please specify r, g, and b values.")
            return
        writer.write_value(KamigamiByteFormatter.get_sendable_light_packet(r=int(user_input[1]), g=int(user_input[2]), b=int(user_input[3])))
    elif user_input[0] == "ir":
        writer.write_value(KamigamiByteFormatter.get_sendable_ir_packet())
    elif user_input[0] == "shutdown":
        writer.write_value(KamigamiByteFormatter.get_sendable_shutdown())
    elif user_input[0] == "testmode":
        # Without one argument, break out
        if len(user_input[1:]) < 1:
            print("Please specify a testmode speed.")
            return
        writer.write_value(KamigamiByteFormatter.get_sendable_testmode(int(user_input[1])))
    elif user_input[0][0:4] == "exit":
        # Kill current process to exit hard.
        os.kill(os.getpid(), signal.SIGINT)
    else:
        print("Unknown command.")

parser = argparse.ArgumentParser()


parser.add_argument('-t', '--time', action='store',
                    help='Customize the time.  Default 10 seconds.')  

parser.add_argument('-m', '--mac', action='store',
                    help='Supply the mac address.')

def find_mac_address():
    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)
     
        def handleDiscovery(self, dev, isNewDev, isNewData):
            pass

    # TODO: Auto Mac Address Finding.

    scanner = Scanner().withDelegate(ScanDelegate())

    try:
        scan_time = float(parser.parse_args().time)
    except Exception:
        scan_time = 10.0

    devices = scanner.scan(scan_time)

    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if value == "KRB0001":
                return dev.addr    


try:
    print("Attempting to connect to Mac Address: " + parser.parse_args().mac)
    MAC_ADDR = parser.parse_args().mac
except:
    MAC_ADDR = find_mac_address()

p = btle.Peripheral(MAC_ADDR, addrType=btle.ADDR_TYPE_RANDOM)

print("Aquired peripheral.")

# Setup to turn notifications on, e.g.

service = p.getServiceByUUID(KamigamiRobot.MAIN_SERVICE_UUID)

writer = service.getCharacteristics(KamigamiRobot.WRITE_UUID)[0]

#print("Starting CLI....")
#while True:
#    val = cli_input()

time.sleep(10)
