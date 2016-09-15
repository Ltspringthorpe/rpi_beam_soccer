from __future__ import print_function
from bluepy.btle import Scanner, DefaultDelegate
import argparse

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        pass

parser = argparse.ArgumentParser()

# TODO: Auto Mac Address Finding.
parser.add_argument('-t', '--time', action='store',
                    help='Customize the time.  Default 10 seconds.')

parser.add_argument('-p', '--passing', action='store_true',
                    help='Output in a way that is easy to be used by other programs.  Similar to git plumbing vs porcelain commands.')

scanner = Scanner().withDelegate(ScanDelegate())

try:
	scan_time = float(parser.parse_args().time)
except Exception:
	scan_time = 10.0

try:
    shouldPass = parser.parse_args().passing
except:
    shouldPass = False

devices = scanner.scan(scan_time)

for dev in devices:
    for (adtype, desc, value) in dev.getScanData():
        if value == "KRB0001":
            # Print it human friendly if not shouldPass
            if not shouldPass:
                print("Found a Kamigami Robot! MAC: " + dev.addr)
            else:
                # Break at the end to print only 1
                print(dev.addr)
                break

dev.addr
