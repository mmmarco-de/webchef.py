# webchef.py

import socket
import os
import threading
import mimetypes
import time
import datetime

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 8080
WEB_ROOT = os.getcwd()

request_count = 0
request_count_lock = threading.Lock()

start_time = None
stop_time = None

# Global list to track paths of index.html files created by webchef.py
_created_index_files = []

# --- MIME Types Mapping ---
def get_mime_type(file_path):
    """Determines the MIME type based on file extension."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type if mime_type else 'application/octet-stream'

def handle_request(client_socket):
    """Handles a single client connection and request."""
    global request_count
    try:
        request_data_bytes = client_socket.recv(4096)
        if not request_data_bytes:
            return

        request_data = request_data_bytes.decode('utf-8')

        request_lines = request_data.split('\r\n')
        if not request_lines or not request_lines[0]:
            send_error(client_socket, 400, "Bad Request")
            return

        first_line = request_lines[0]
        parts = first_line.split(' ')

        if len(parts) < 3:
            send_error(client_socket, 400, "Bad Request")
            return

        method, path, http_version = parts[0], parts[1], parts[2]

        print(f"👨‍🍳 Request: {method} {path} {http_version}")

        if method == 'GET':
            if '..' in path or path.startswith('/.') or path.endswith('/.'):
                send_error(client_socket, 403, "Forbidden")
                return

            if path == '/':
                requested_file_relative = 'index.html'
                requested_dir_absolute = WEB_ROOT
            else:
                requested_file_relative = path[1:]
                requested_dir_absolute = os.path.join(WEB_ROOT, os.path.dirname(requested_file_relative))

            requested_file_absolute = os.path.join(WEB_ROOT, requested_file_relative)

            if os.path.isdir(requested_file_absolute):
                requested_file_absolute = os.path.join(requested_file_absolute, 'index.html')
                requested_dir_absolute = os.path.dirname(requested_file_absolute)

            if os.path.exists(requested_file_absolute) and os.path.isfile(requested_file_absolute):
                mime_type = get_mime_type(requested_file_absolute)
                send_response(client_socket, 200, "OK", mime_type, requested_file_absolute)
            else:
                print(f"Ingredient not found: {requested_file_absolute}")
                send_error(client_socket, 404, "Not Found")
        else:
            send_error(client_socket, 501, "Not Implemented")
    except ConnectionResetError:
        print("Client left the kitchen unexpectedly. 💔")
    except Exception as e:
        print(f"Oops! A kitchen mishap: {e}")
        send_error(client_socket, 500, "Internal Server Error")
    finally:
        client_socket.close()
        with request_count_lock:
            request_count += 1

def send_response(client_socket, status_code, status_message, content_type, file_path):
    """Sends an HTTP response with file content."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()

        headers = [
            f"HTTP/1.1 {status_code} {status_message}",
            f"Content-Type: {content_type}",
            f"Content-Length: {len(content)}",
            "Connection: close",
            "\r\n"
        ]
        response_headers = "\r\n".join(headers).encode('utf-8')

        client_socket.sendall(response_headers)
        client_socket.sendall(content)
        print(f"✅ Dish served: {status_code} {status_message} for {os.path.basename(file_path)}")
    except FileNotFoundError:
        print(f"Error: Ingredient missing when preparing dish: {file_path}")
        send_error(client_socket, 404, "Not Found")
    except Exception as e:
        print(f"Error serving the dish for {file_path}: {e}")
        send_error(client_socket, 500, "Internal Server Error")

def send_error(client_socket, status_code, status_message):
    """Sends an HTTP error response with a kitchen-themed error page."""
    error_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error {status_code}</title>
        <style>
            body {{
                background-color: #333;
                color: #eee;
                font-family: 'Inter', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }}
            .container {{
                text-align: center;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                background-color: #444;
            }}
            h1 {{
                font-size: 2em;
                margin-bottom: 20px;
                color: #ff6b6b;
                border-bottom: 2px solid #ff6b6b;
                padding-bottom: 10px;
            }}
            p {{
                font-size: 1.1em;
                margin-bottom: 15px;
            }}
            .emoji {{
                font-size: 3em;
                margin-right: 10px;
                vertical-align: middle;
            }}
            a {{
                color: #bbb;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1><span class="emoji">🔥</span> Kitchen Fire! Error {status_code}: {status_message} <span class="emoji">🔥</span></h1>
            <p>Looks like we couldn't find that recipe or something went wrong in the kitchen.</p>
            <p>Please check your ingredients (URL) and try again!</p>
        </div>
    </body>
    </html>
    """.strip()

    error_content_bytes = error_content.encode('utf-8')

    headers = [
        f"HTTP/1.1 {status_code} {status_message}",
        "Content-Type: text/html; charset=utf-8",
        f"Content-Length: {len(error_content_bytes)}",
        "Connection: close",
        "\r\n"
    ]
    response_headers = "\r\n".join(headers).encode('utf-8')

    try:
        client_socket.sendall(response_headers)
        client_socket.sendall(error_content_bytes)
        print(f"❌ Sent error {status_code} {status_message}")
    except Exception as e:
        print(f"Failed to send error response: {e}")
    finally:
        client_socket.close()

def create_all_missing_index_htmls(root_dir):
    """
    Creates default index.html files in the root directory and all subdirectories
    if they don't already exist.
    """
    global _created_index_files
    print("🧑‍🍳 Scanning directories for missing index.html files...")
    for dirpath, dirnames, filenames in os.walk(root_dir):
        index_path = os.path.join(dirpath, 'index.html')
        if not os.path.exists(index_path):
            relative_dir_display = os.path.relpath(dirpath, root_dir)
            if relative_dir_display == '.':
                relative_dir_display = './'

            print(f"🧑‍🍳 No index.html found in '{relative_dir_display}'. Whipping up a default one...")
            default_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>webchef.py - Index of {os.path.basename(dirpath) if dirpath != root_dir else 'Root'}</title>
                <style>
                    body {{
                        background-color: #333;
                        color: #eee;
                        font-family: 'Inter', sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                    }}
                    .container {{
                        text-align: center;
                        border-radius: 10px;
                        padding: 30px;
                        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
                        background-color: #444;
                    }}
                    h1 {{
                        font-size: 2em;
                        margin-bottom: 20px;
                        color: #90caf9;
                        border-bottom: 2px solid #90caf9;
                        padding-bottom: 15px;
                    }}
                    p {{
                        font-size: 1.2em;
                        margin-bottom: 15px;
                    }}
                    .directory-list {{
                        list-style-type: none;
                        padding: 0;
                        max-width: 600px;
                        margin: 20px auto;
                        text-align: left;
                    }}
                    .directory-list li {{
                        background-color: #555;
                        margin-bottom: 8px;
                        padding: 10px 15px;
                        border-radius: 5px;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    }}
                    .directory-list li a {{
                        color: #bbb;
                        text-decoration: none;
                        font-weight: bold;
                    }}
                    .directory-list li a:hover {{
                        text-decoration: underline;
                        color: #fff;
                    }}
                    .icon {{
                        font-size: 1.2em;
                        margin-right: 10px;
                        vertical-align: middle;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Welcome to your webchef.py Kitchen! 🧑‍🍳</h1>
                    <p>No <code>index.html</code> found here, so I've cooked up this default page for you.</p>
                    <p>Here's what's currently on the menu in <code>{relative_dir_display}</code>:</p>
                    <ul class="directory-list">
            """
            # Add parent directory link if not the root directory
            if dirpath != root_dir:
                default_content += f'<li><span class="icon">⬆️</span><a href="../">../ (Parent Directory)</a></li>\n'

            # List current directory contents
            for item in sorted(os.listdir(dirpath)):
                item_full_path = os.path.join(dirpath, item)
                icon = ""
                link_text = item
                href_target = item

                if os.path.isfile(item_full_path):
                    icon = "📄"
                elif os.path.isdir(item_full_path):
                    icon = "📁"
                    link_text = item + "/"
                    href_target = item + "/"
                else:
                    icon = "❓"

                # Exclude webchef.py itself and hidden files/folders (starting with '.')
                if item == os.path.basename(__file__) or item.startswith('.'):
                    continue

                default_content += f'<li><span class="icon">{icon}</span><a href="{href_target}">{link_text}</a></li>\n'

            default_content += """
                    </ul>
                    <p>Start cooking by adding your own <code>index.html</code>!</p>
                </div>
            </body>
            </html>
            """
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(default_content)
            _created_index_files.append(index_path)
            print(f"Default index.html created in '{relative_dir_display}'. 😋")
        else:
            print(f"Index.html already exists in '{relative_dir_display}'. Skipping. 👍")

def cleanup_generated_index_files():
    """Deletes all index.html files that were created by webchef.py."""
    global _created_index_files
    if _created_index_files:
        print("\n🗑️ Cleaning up generated index.html files...")
        for file_path in _created_index_files:
            try:
                os.remove(file_path)
                print(f"Deleted: {os.path.relpath(file_path, WEB_ROOT)}")
            except OSError as e:
                print(f"Error deleting {os.path.relpath(file_path, WEB_ROOT)}: {e}")
        _created_index_files = []
        print("Cleanup complete. ✨")
    else:
        print("No generated index.html files to clean up. 🧹")


def main():
    """Main function to start the HTTP server."""
    global start_time, stop_time

    start_time = datetime.datetime.now()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"✨ webchef.py is cooking! Serving on http://{HOST}:{PORT}")
        print(f"🏡 Your kitchen (root directory): {os.path.abspath(WEB_ROOT)}")

        # Create default index.html files in all directories that need them
        create_all_missing_index_htmls(WEB_ROOT)

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Customer arrived from {client_address[0]}:{client_address[1]} 🚶")
            client_handler = threading.Thread(target=handle_request, args=(client_socket,))
            client_handler.start()

    except KeyboardInterrupt:
        print("\n🛑 Closing the kitchen for the day... 😴")
        stop_time = datetime.datetime.now()
    except Exception as e:
        print(f"🚨 Critical kitchen failure: {e}")
        stop_time = datetime.datetime.now()
    finally:
        server_socket.close()
        print("Kitchen closed. 🚪")
        cleanup_generated_index_files()
        generate_receipt()

def generate_receipt():
    """Generates and prints a kitchen-themed receipt with server details."""
    if start_time is None:
        print("Server did not start correctly, no receipt to generate.")
        return

    if stop_time is None:
        current_time = datetime.datetime.now()
        uptime_seconds = (current_time - start_time).total_seconds()
    else:
        uptime_seconds = (stop_time - start_time).total_seconds()

    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    print("\n" + "="*40)
    print("           🧾 webchef.py Receipt 🧾")
    print("="*40)
    print(f"Server Name:        webchef.py")
    print(f"Date Started:       {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Date Stopped:       {stop_time.strftime('%Y-%m-%d %H:%M:%S') if stop_time else 'Still Cooking!'}")
    print(f"Total Uptime:       {int(hours)}h {int(minutes)}m {int(seconds)}s")
    print(f"Serving Table (Port): {PORT}")
    print(f"Kitchen Location (Root): {os.path.abspath(WEB_ROOT)}")
    print(f"Dishes Served (Requests): {request_count}")
    print("-" * 40)
    print("Thank you for dining with webchef.py! 🙏 Come again soon! 💖")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
