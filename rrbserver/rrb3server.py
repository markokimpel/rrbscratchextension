'''
RasPiRobot Board V3 Server

HTTP interface to the Python API of the Raspberry Pi board RasPiRobot Board V3 (RRB3).

User pages:
    /                 homepage
    /controller.html  UI to manually control RRB3

Scratch extension:
    /scratch_extension.js

Web services (request/response format is JSON):
    GET  /ping
         { "server": "rrb3", "v1": "supported" }
    GET  /v1/ping
         { "server": "rrb3" }
    POST /v1/led/[led_no] { "state": "on"|"off" }
    GET  /v1/switch/[switch_no]
         { "state": "open" | "closed" }
    POST /v1/move { "direction": "forward"|"reverse"|"right"|"left", "speed": [pct], "duration": [secs] }
    POST /v1/motors { left_direction: "forward"|"reverse", "left_speed": [pct], "right_direction"="forward"|"reverse", "right_speed": [pct] }
    POST /v1/stop
    GET  /v1/distance
         { "distance": [dist] }
'''

import json
from mimetypes import MimeTypes
import os
import socket
import shutil
import urllib

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from rrb3 import RRB3

class RRB3HTTPRequestHandler(BaseHTTPRequestHandler):

    # whitelist of allowed paths
    ALLOWED_DOWNLOADS = {
        "/",
        "/controller.html",
        "/controller.js",
        "/scratch_extension.js",
        "/favicon.ico",
        "/jquery/jquery-3.2.1.min.js",
        "/bootstrap/css/bootstrap.min.css",
        "/bootstrap/js/bootstrap.min.js"}

    def do_GET(self):

        # static file download
        if self.path in self.ALLOWED_DOWNLOADS:

            # strip off leading '/'
            fname = self.path[1:]
            if fname == "":
                fname = "index.html"

            # read file
            with open(fname, "r") as f:
                content = f.read()

            # replace placeholders
            host_port = self.headers.getheader('Host')
            if host_port is None:
                host_port = 'localhost'

            content = content.replace('{{host_port}}', host_port)

            self.send_response(200)

            # set Content-Type
            content_type = MimeTypes().guess_type(fname)[0]
            if content_type is not None:
                self.send_header('Content-Type', content_type + "; charset=UTF-8")
            self.end_headers()

            # send content to requester
            self.wfile.write(content)

        elif self.path == '/ping':
            data = {'server': 'rrb', 'v1': 'supported'}
            self.send_json_response(data)

        elif self.path == '/v1/ping':
            data = {'server': 'rrb'}
            self.send_json_response(data)

        elif self.path.startswith('/v1/switch/'):

            # switch_no from URL
            switch_no = urllib.unquote(self.path[11:])
            if switch_no not in {'1', '2'}:
                self.send_error(400, "Unknown switch_no " + switch_no)
                return

            if switch_no == '1':
                state = rrb3.sw1_closed()
            else:
                state = rrb3.sw2_closed()

            if state == 1:
                state_string = 'closed'
            else:
                state_string = 'open'

            data = {'state' : state_string}
            self.send_json_response(data)

        elif self.path == '/v1/distance':

            distance = rrb3.get_distance()

            data = {'distance' : distance}
            self.send_json_response(data)

        else:
            self.send_error(404, "Unknown path " + self.path)

    def do_POST(self):

        if self.path.startswith('/v1/led/'):

            # read and parse POST data
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(data_string)

            # led_no from URL
            led_no = urllib.unquote(self.path[8:])
            if led_no not in {'1', '2'}:
                self.send_error(400, "Unknown led_no " + led_no)
                return

            # state from POST data
            if data['state'] == 'on':
                state = 1
            elif data['state'] == 'off':
                state = 0
            else:
                self.send_error(400, "Unknown state " + data['state'])
                return

            if led_no == '1':
                rrb3.set_led1(state)
            else:
                rrb3.set_led2(state)

            self.send_json_response({})

        elif self.path == '/v1/move':

            # read and parse POST data
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(data_string)

            # direction from POST data
            direction = data['direction']
            if direction not in {'forward','reverse','right','left'}:
                self.send_error(400, "Unknown direction " + direction)
                return

            if not self.is_convertible_to_float(data['speed']):
                self.send_error(400, "Parameter speed not a float (%s)" % data['speed'])
                return
            speed = float(data['speed'])
            if speed < 0 or speed > 100:
                self.send_error(400, "Parameter speed not in range 0..100 (%f)" % speed)
                return

            if not self.is_convertible_to_float(data['duration']):
                self.send_error(400, "Parameter duration not a float (%s)" % data['duration'])
                return
            duration = float(data['duration'])
            if duration < 0:
                self.send_error(400, "Parameter duration less than 0 (%f)" % duration)
                return

            if direction == 'forward':
                rrb3.forward(duration, speed / 100)
            elif direction == 'reverse':
                rrb3.reverse(duration, speed / 100)
            elif direction == 'right':
                rrb3.right(duration, speed / 100)
            else:
                rrb3.left(duration, speed / 100)

            self.send_json_response({})

        elif self.path == '/v1/motors':

            # read and parse POST data
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            data = json.loads(data_string)

            if data['left_direction'] == 'forward':
                left_direction = 0
            elif data['left_direction'] == 'reverse':
                left_direction = 1
            else:
                self.send_error(400, "Unknown left_direction " + data['left_direction'])
                return

            if not self.is_convertible_to_float(data['left_speed']):
                self.send_error(400, "Parameter left_speed not a float (%s)" % data['left_speed'])
                return
            left_speed = float(data['left_speed'])
            if left_speed < 0 or left_speed > 100:
                self.send_error(400, "Parameter left_speed not in range 0..100 (%f)" % left_speed)
                return

            if data['right_direction'] == 'forward':
                right_direction = 0
            elif data['right_direction'] == 'reverse':
                right_direction = 1
            else:
                self.send_error(400, "Unknown right_direction " + data['right_direction'])
                return

            if not self.is_convertible_to_float(data['right_speed']):
                self.send_error(400, "Parameter right_speed not a float (%s)" % data['right_speed'])
                return
            right_speed = float(data['right_speed'])
            if right_speed < 0 or right_speed > 100:
                self.send_error(400, "Parameter right_speed not in range 0..100 (%f)" % right_speed)
                return

            rrb3.set_motors(right_speed / 100, right_direction, left_speed / 100, left_direction)

            self.send_json_response({})

        elif self.path == '/v1/stop':

            rrb3.stop()

            self.send_json_response({})

        else:
            self.send_error(404, "Unknown path " + self.path)

    def do_OPTIONS(self):

        # needed for CORS pre-flight requests

        if self.headers.getheader('Origin') is None:
            self.send_error(501, "Non-CORS OPTIONS request not implemented")
            return

        self.send_response(200)

        self.send_header("Access-Control-Allow-Origin", self.headers.getheader('Origin'))
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

        if self.headers.getheader('Access-Control-Request-Headers') is not None:
            self.send_header("Access-Control-Allow-Headers", self.headers.getheader('Access-Control-Request-Headers'))

        self.end_headers()

    def send_json_response(self, data):
        data_string = json.dumps(data)
        self.send_response(200)
        if self.headers.getheader('Origin') is not None:
            self.send_header("Access-Control-Allow-Origin", self.headers.getheader('Origin'))
        self.send_header("Content-Type", "application/json; charset=UTF-8")
        self.end_headers()
        self.wfile.write(data_string)

    def is_convertible_to_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

# Try to find own ip address by establishing connection to arbitrary host
# (without sending data).
def get_own_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        # fallback
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == "__main__":

    # TODO: make port configurable
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, RRB3HTTPRequestHandler)

    # should always print IP address '0.0.0.0' which means listing at all IPs
    print("Server listening at " + httpd.server_address[0] + ":" + str(httpd.server_address[1]))
    print("")

    own_ip = get_own_ip()
    print("RRB3 Server homepage : http://" + own_ip + ":" + str(httpd.server_address[1]) + "/")
    print("Scratch extension URL: http://" + own_ip + ":" + str(httpd.server_address[1]) + "/scratch_extension.js")
    print("")

    print("Press Ctrl-C to stop server")

    rrb3 = RRB3()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        rrb3.cleanup()
