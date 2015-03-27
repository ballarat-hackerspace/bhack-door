#!/usr/bin/env python3
import time

from os import curdir
from os.path import join as pjoin

from http.server import BaseHTTPRequestHandler, HTTPServer


testing = False

if not testing:
    import pifacerelayplus


class StoreHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/open':
            if not testing:
                pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
                pfr.relays[0].toggle()
            self.send_message("Hack away")

        elif self.path == "/close":
            if not testing:
                pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
            self.send_message("Door shut")

        elif self.path.startswith("/enter"):
            time_to_sleep = 3
            if not testing:
                pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)
                pfr.relays[0].toggle()
                time.sleep(time_to_sleep)
                pfr.relays[0].toggle()
            self.send_message("Hack away, door will shut behind you in {} seconds".format(time_to_sleep))

        elif self.path == "/status":
            status = str(testing)
            self.send_message(status)

    def do_POST(self):
        return do_GET(self)
        
    def send_message(self, message):
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        #self.wfile.write('"{0}"'.format(message).encode())
        self.wfile.write(message.encode())
        

server = HTTPServer(('', 8080), StoreHandler)
server.serve_forever()

