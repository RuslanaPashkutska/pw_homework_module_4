import socket

def main():
    host = socket.gethostname()
    print(host)
    port = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))


    conn, address = server_socket
    print(f"Connection from {address}")
    while True:
        msg = conn.recv(1014).decode()
        if not msg:
            break
        print(f"Received message: {msg}")
        message = input(">>> ")
        conn.send(message.encode())
    conn.close()
    server_socket.close()


if __name__ == "__main__":
    main()