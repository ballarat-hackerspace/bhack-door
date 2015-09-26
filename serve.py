#!/usr/bin/env python3

from socketserver import ThreadingMixIn
from http.server import SimpleHTTPRequestHandler, HTTPServer

class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass

import ssl
import sys
import json
import time
import syslog
import threading
import configparser
import http.client
import urllib.parse

from os import curdir
from os.path import join as pjoin

testing = False

if not testing:
    import pifacerelayplus
    pfr = pifacerelayplus.PiFaceRelayPlus(pifacerelayplus.RELAY)

    # enable cooling on boot up
    pfr.relays[3].value = 1

#
# DOOR WATCHER
#
door_watcher = False
door_watcher_thread = None
def door_state_set(state, duration=5):
    global door_watcher

    # set the relay value
    if not testing:
        pfr.relays[0].value = state

    # reset to 0 after duration if set
    if duration > 0:
        time.sleep(duration)
        if not testing:
            pfr.relays[0].value = 0

    door_watcher = False


def door_control(state, duration=5):
    global door_watcher
    global door_watcher_thread

    # early return if watcher is set
    if door_watcher:
        return False

    door_watcher = True
    door_watcher_thread = threading.Thread(target=door_state_set, args=(state, duration))
    door_watcher_thread.daemon = True
    door_watcher_thread.start()

    # cap max duration to 5 seconds
    duration = min(int(duration), 5)

    return True

class DoorHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        syslog.syslog("do_GET: %s" % self.path)
        o = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(o.query)

        if self.path == '/open':
            if door_control(1, 0):
                self.slack_api("Door function close has been executed.")
                self.send_message({"message": "Hack away"})

            else:
                self.send_message({"message": "Door is busy, try again shortly!"}, 503)


        elif self.path == "/close":
            if door_control(0, 0):
                self.slack_api("close")
                self.send_message({"message": "Door shut"})
            else:
                self.send_message({"message": "Door is busy, try again shortly!"}, 503)


        elif self.path.startswith("/enter"):
            time_to_sleep = 5
            if door_control(1, time_to_sleep):
                mac  = query.get('mac', ['???'])[0]
                user = query.get('user', ['unknown'])[0]
                name = query.get('name', ['unknown'])[0]
                print(mac, user, name)
                self.send_message({"message": "Hack away, door will shut behind you in {} seconds".format(time_to_sleep)})
                self.slack_api("Door function enter has been executed by {0} on {1} ({2}).".format(user, name, mac))

            else:
                self.send_message({"message": "Door is busy, try again shortly!"}, 503)

        elif self.path == "/status":
            if testing:
                status = -1
            else:
                status = pfr.relays[0].value
            self.send_message({"status": status})
            self.slack_api("Door function status has been executed.")

        elif self.path == "/ping":
            self.send_message({"pong": True})

        else:
            self.send_message({"message":"This is not the end point you're looking for"}, 404)

    def slack_api(self, msg):
        if testing:
            return

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

        params = urllib.parse.urlencode({'payload': '{ "channel": "%s", "username": "%s", "icon_emoji": "%s", "text": "%s" }' % (channel, username, icon, msg) })

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
        self.wfile.flush()

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

Config = configparser.ConfigParser()
Config.read("/srv/door.bhack/bhack-door/serve.ini")

port = 8080

if (len(sys.argv) > 1):
    port = int(sys.argv[1])

syslog.syslog("Listening to port: %s" % port)

server = ThreadingSimpleServer(('', port), DoorHandler)
try:
    while 1:
        sys.stdout.flush()
        server.handle_request()
except:
    print("Finished")

