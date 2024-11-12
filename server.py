import socket
from threading import Thread


def new_connection(addr, client_socket):
    print(client_socket)
    message = client_socket.recv(1024).decode('utf-8')
    if message == 'File A':
        with open('simple_client.py', 'r') as file:
            file_content = file.read()  # Read the file into a string
        client_socket.send(file_content.encode('utf-8'))
    elif message == 'File B':
        with open('server.py', 'r') as file:
            file_content = file.read()
        client_socket.send(file_content.encode('utf-8'))


#Just return the IP address of the interface
#that is used to send the packet to the
#default gateway
def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def server_program(server_host, server_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_host, server_port))

    server_socket.listen(10)
    while True:
        client_socket, addr = server_socket.accept()
        client_thread = Thread(target=new_connection, args=(addr, client_socket))
        client_thread.start()


if __name__ == '__main__':
    host = get_host_default_interface_ip()
    port = 8080
    print("Listening on: {}:{}".format(host, port))
    server_program(host, port)