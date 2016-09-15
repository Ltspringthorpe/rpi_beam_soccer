import argparse
import time
from subprocess import check_output
from bluepy import btle
from KamigamiData import *
from KamigamiInterface import KamigamiInterface

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


parser = argparse.ArgumentParser()

# TODO: Auto Mac Address Finding.
parser.add_argument('-m', '--mac', action='store',
                    help='Supply the mac address.') 

try:
	print("Attempting to connect to Mac Address: " + parser.parse_args().mac)
	MAC_ADDR = parser.parse_args().mac
except:
	print("Scanning for Robot and connecting to the first one.")
	import os
	if "mac_scanner.py" not in os.listdir("."):
		raise EnvironmentError("Mac address must be specified if the scanner is not in the directory.")
	MAC_ADDR = check_output(["sudo", "python", "mac_scanner.py", "-p", "-t", "5.0"])[:17]


p = btle.Peripheral(MAC_ADDR, addrType=btle.ADDR_TYPE_RANDOM)

print("Aquired peripheral.")

# Setup to turn notifications on, e.g.

service = p.getServiceByUUID(KamigamiRobot.MAIN_SERVICE_UUID)

writer = service.getCharacteristics(KamigamiRobot.WRITE_UUID)[0]

interface = KamigamiInterface(None, AdaptedWriter(writer))
interface.run()


time.sleep(10)
