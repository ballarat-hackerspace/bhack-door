#!/usr/bin/env python3

import sys, getopt
import syslog
import pifacerelayplus

def main(argv):
   pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
   state = None
   try:
      opts, args = getopt.getopt(argv,"f:",["fan="])
   except getopt.GetoptError:
      print("fan.py -f <on|off>")
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print("fan.py -f <on|off>")
         sys.exit()
      elif opt in ("-f", "--fan"):
         state = arg
   if state == "on":
      pfr.relays[3].value = 1
   elif state == "off":
      pfr.relays[3].value = 0
   else:
      print("fan.py -f <on|off>")
      sys.exit(2)
   sys.exit(0)

if __name__ == "__main__":
   main(sys.argv[1:])
