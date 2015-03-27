#!/usr/bin/env python3
import json
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
                pfr.relays[0].value = 1
            self.send_message({"message": "Hack away"})

        elif self.path == "/close":
            if not testing:
                pfr.relays[0].value = 0
            self.send_message({"message": "Door shut"})

        elif self.path.startswith("/enter"):
            time_to_sleep = 3
            if not testing:
                pfr.relays[0].value = 1
                time.sleep(time_to_sleep)
                pfr.relays[0].value = 0
            self.send_message({"message": "Hack away, door will shut behind you in {} seconds".format(time_to_sleep)})

        elif self.path == "/status":
            if testing:
                status = -1
            else:
                status = pfr.relays[0].value
            self.send_message({"status": status})

        else:
            self.send_message({"message":"This is not the end point you're looking for"}, 404)


    def do_POST(self):
        return do_GET(self)
        
    def send_message(self, message, response=200):
        self.send_response(response)
        self.send_header('Cache-control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(message).encode())


if not testing:
    pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)

server = HTTPServer(('', 8080), StoreHandler)
server.serve_forever()

