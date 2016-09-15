from KamigamiData import *
import time

"""
Edit this file to specify actions.  This interface file allows you to 
read and write values to the robot without changing KamigamiConnection.
Note that the read_manager argument is currently in place only to make 
the interface completely compatible with both mac and linux.  It is currently
unimplemented for linux and will be passed as None.
"""

class KamigamiInterface:
	def __init__(self, read_manager, write):
		self.write = write
		self.read_manager = read_manager

	# Implement me
	def run(self):
		raise NotImplementedError
