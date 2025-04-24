# Project: webchef.py
# Author: Marco (marco@mmmarco.de)
# License: Unlicense
# Last updated: 24. Apr 2025
# Version: 0.2.0

import http.server
import socketserver
import os
import time
import logging

# --- Recipe (Default Configuration) ---
RECIPE = {
    "kitchen_address": "127.0.0.1",  # The Chef's serving station address
    "oven_port": 8000,               # The oven's serving port
    "menu_directory": ".",           # Where the Chef keeps the menu
    "log_level": logging.ERROR       # How much noise from the kitchen
}

# --- 404 Dish Location ---
NOT_FOUND_DISH = "webchef.404.html"

class WebChefHandler(http.server.SimpleHTTPRequestHandler):
    def send_header(self, keyword, value):
        """Override to prevent default Server header."""
        if keyword != 'Server':
            super().send_header(keyword, value)

    def do_GET(self):
        path = self.path.lstrip('/')

        if not path:
            path = 'index.html'

        filepath = os.path.join(self.server.menu_directory, path)

        try:
            if os.path.isdir(filepath):
                index_path = os.path.join(filepath, 'index.html')
                if os.path.exists(index_path) and os.path.isfile(index_path):
                    self.path = os.path.join('/', path, 'index.html')
                    self.send_response(200)
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    return http.server.SimpleHTTPRequestHandler.do_GET(self)
                else:
                    self.send_error(404)
                    return
            elif os.path.exists(filepath) and os.path.isfile(filepath):
                self.send_response(200)
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.path = '/' + path
                return http.server.SimpleHTTPRequestHandler.do_GET(self)
            elif os.path.exists(filepath + '.html') and os.path.isfile(filepath + '.html'):
                self.send_response(200)
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.path = '/' + path + '.html'
                return http.server.SimpleHTTPRequestHandler.do_GET(self)
            else:
                self.send_error(404)
                return
        except BrokenPipeError:
            self.log_error("Broken pipe during request: %s", self.path)
        except ConnectionResetError:
            self.log_error("Connection reset during request: %s", self.path)

    def send_error(self, code, message=None):
        self.log_error('"%s" %s', self.requestline, str(code))
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), NOT_FOUND_DISH)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as f:
                    content = f.read()
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Content-Length', str(len(content)))
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    self.end_headers()
                    self.wfile.write(content)
            except IOError:
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                self.send_header('Pragma', 'no-cache')
                self.send_header('Expires', '0')
                self.end_headers()
                self.wfile.write(b"File Not Found")
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.end_headers()
            self.wfile.write(b"File Not Found")

if __name__ == "__main__":
    print("Welcome to Webchef's Restaurant!")
    print("Your order of 1x Web Server has been placed.")

    host = RECIPE["kitchen_address"]
    port = RECIPE["oven_port"]
    menu_directory = RECIPE["menu_directory"]
    logging.basicConfig(level=RECIPE["log_level"])

    with socketserver.TCPServer((host, port), WebChefHandler) as server:
        server.menu_directory = menu_directory
        print(f"The Web Server has been served by the Chef at table {port}.")
        start_time = time.time()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time))
            print("\nVVVVVVVVVVVVVVVVVVVVVVVVVV")
            print("| RECEIPT")
            print("| ==========")
            print("| Webchef's Restaurant")
            print(f"| http://{host}")
            print("| ")
            print(f"| Table: {port}")
            print(f"| Uptime: {uptime}")
            print("| ")
            print("| Web Server has been stopped.")
            print("| ")
            print("VVVVVVVVVVVVVVVVVVVVVVVVVV")