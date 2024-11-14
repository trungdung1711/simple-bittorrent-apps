import socket


try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('192.168.0.110', 50000))

    # Application connection created

    print('check - send request')

    client_socket.send('REQUEST'.encode('utf-8'))

    print('check - sent')

    print(client_socket.recv(2048).decode('utf-8'))

    print('check - received')
    client_socket.close()
except Exception as e:
    print('My application ' + e.get_message())