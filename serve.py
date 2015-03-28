#!/usr/bin/env python3

import ssl
import sys
import json
import time
import syslog
import configparser
import http.client
import urllib.parse

from os import curdir
from os.path import join as pjoin

from http.server import BaseHTTPRequestHandler, HTTPServer

testing = False

if not testing:
    import pifacerelayplus

class StoreHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        syslog.syslog("do_GET: %s" % self.path)

        if self.path == '/open':
            if not testing:
                pfr.relays[0].value = 1
            self.send_message({"message": "Hack away"})
            self.slack_api("open")

        elif self.path == "/close":
            if not testing:
                pfr.relays[0].value = 0
            self.send_message({"message": "Door shut"})
            self.slack_api("close")

        elif self.path.startswith("/enter"):
            time_to_sleep = 3
            if not testing:
                pfr.relays[0].value = 1
                time.sleep(time_to_sleep)
                pfr.relays[0].value = 0
            self.send_message({"message": "Hack away, door will shut behind you in {} seconds".format(time_to_sleep)})
            self.slack_api("enter")

        elif self.path == "/status":
            if testing:
                status = -1
            else:
                status = pfr.relays[0].value
            self.send_message({"status": status})
            self.slack_api("status")

        else:
            self.send_message({"message":"This is not the end point you're looking for"}, 404)

    def slack_api(self, msg):
        syslog.syslog("slack_api")
        host = ConfigSectionMap('slack')['host']
        path = ConfigSectionMap('slack')['path']
        channel = ConfigSectionMap('slack')['channel']
        username = ConfigSectionMap('slack')['username']
        icon = ConfigSectionMap('slack')['icon_emoji']

        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations('/etc/ssl/certs/ca-certificates.crt')
        conn = http.client.HTTPSConnection(host, 443, context=context)

        params = urllib.parse.urlencode({'payload': '{ "channel": "%s", "username": "%s", "icon_emoji": "%s", "text": "Door function %s has been executed." }' % (channel, username, icon, msg) })

        conn.request("POST", path, params, headers)
        response = conn.getresponse()
        syslog.syslog("Slack API response: %s %s" % (response.status, response.reason))
        data = response.read()
        conn.close()

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


def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

if not testing:
    pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)

Config = configparser.ConfigParser()
Config.read("/home/pi/bhack-door/serve.ini")

port = 8080

if (len(sys.argv) > 1):
    port = int(sys.argv[1])

syslog.syslog("Listening to port: %s" % port)

server = HTTPServer(('', port), StoreHandler)
server.serve_forever()

