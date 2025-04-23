# Project: webchef.py
# Author: Marco (marco@mmmarco.de)
# License: Unlicense
# Last updated: 23. Apr 2025
# Version: 0.1.0

import http.server
import socketserver
import json
import os
import time
import logging

# --- Default Recipe (Configuration) ---
DEFAULT_RECIPE = {
    "kitchen_address": "127.0.0.1",  # The Chef's serving station address
    "oven_port": 8000,               # The oven's serving port
    "menu_directory": ".",           # Where the Chef keeps the menu
    "log_level": logging.ERROR       # How much noise from the kitchen
}

# --- Custom Recipe Location ---
CUSTOM_RECIPE_FILE = "webchef.config"

# --- 404 Dish Location ---
NOT_FOUND_DISH = "webchef.404.html"

class WebChefHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.lstrip('/')

        if not path:
            path = 'index.html'

        filepath = os.path.join(self.server.menu_directory, path)

        if os.path.isdir(filepath):
            index_path = os.path.join(filepath, 'index.html')
            if os.path.exists(index_path) and os.path.isfile(index_path):
                self.path = os.path.join('/', path, 'index.html')
                return http.server.SimpleHTTPRequestHandler.do_GET(self)
            else:
                self.send_error(404)
                return
        elif os.path.exists(filepath) and os.path.isfile(filepath):
            self.path = '/' + path
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif os.path.exists(filepath + '.html') and os.path.isfile(filepath + '.html'):
            self.path = '/' + path + '.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        else:
            self.send_error(404)
            return

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
                    self.end_headers()
                    self.wfile.write(content)
            except IOError:
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"404 Page Not Found")
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"404 Page Not Found")

def load_recipe():
    recipe = DEFAULT_RECIPE
    if os.path.exists(CUSTOM_RECIPE_FILE):
        try:
            with open(CUSTOM_RECIPE_FILE, 'r') as f:
                custom_recipe = json.load(f)
                recipe.update(custom_recipe)
                logging.info("Custom recipe loaded from %s", CUSTOM_RECIPE_FILE)
        except json.JSONDecodeError:
            logging.error("Error decoding custom recipe. Using default.")
        except FileNotFoundError:
            logging.warning("Custom recipe file not found. Using default.")
    return recipe

if __name__ == "__main__":
    print("Welcome to Webchef's Restaurant!")
    print("Your order of 1x Web Server has been placed.")

    recipe = load_recipe()
    host = recipe["kitchen_address"]
    port = recipe["oven_port"]
    menu_directory = recipe["menu_directory"]
    logging.basicConfig(level=recipe["log_level"])

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
            print("\nRECEIPT")
            print("==========")
            print("Webchef's Restaurant")
            print(f"http://{host}")
            print("")
            print(f"Table: {port}")
            print(f"Uptime: {uptime}")
            print("")
            print("")
            print("Web Server has been stopped.")