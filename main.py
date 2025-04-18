import logging
import mimetypes
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import socket
import json
from datetime import datetime


BASE_DIR = Path(__file__).parent
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = "0.0.0.0"
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 5000


class GoItFramwork(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html("index.html")
            case "/message.html":
                self.send_html("message.html")
            case _ if route.path.startswith("/static/"):
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html", 404)


    def do_POST(self):
        size = self.headers.get("Content-Length", 0)
        data = self.rfile.read(int(size))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header("Location", "/message.html")
        self.end_headers()


    def send_html(self, filename, status_code=200):
        file = BASE_DIR / filename
        if file.exists():
            self.send_response(status_code)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open(filename, "rb") as file:
                self.wfile.write(file.read())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open(BASE_DIR / "error.html", "rb") as error_file:
                self.wfile.write(error_file.read())




    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-Type", mime_type)
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()
        with open(BASE_DIR / filename, "rb") as file:
            self.wfile.write(file.read())

def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        parse_dict = {key: value for key, value in [el.split("=") for el in parse_data.split("&")]}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        new_message = {
            timestamp: {
                "username": parse_dict.get("username", ""),
                "message": parse_dict.get("message", "")
            }
        }
        data_path = BASE_DIR / "storage/data.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        if data_path.exists():
            with open(data_path, "r", encoding="utf-8") as file:
                all_data = json.load(file)
        else:
            all_data = {}

        all_data.update(new_message)

        with open("storage/data.json", "w", encoding="utf-8") as file:
            json.dump(all_data, file, ensure_ascii=False, indent=4)

    except json.JSONDecodeError as err:
        logging.error(f"JSON decode error: {err}")
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)

def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg} ")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        logging.info("Socket server stopped by user")
    finally:
        server_socket.close()


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, GoItFramwork)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s %(message)s")

    storage_dir = BASE_DIR / "storage"
    data_file = storage_dir / "data.json"
    if not storage_dir.exists():
        logging.debug("Creating storage directory...")
        storage_dir.mkdir(parents=True)

    if not data_file.exists():
        logging.debug("Creating empty data.json file...")
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump({}, f,ensure_ascii=False, indent=4)

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
