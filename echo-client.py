#!/usr/local/bin/python3.8

import socket

HOST = "::1"
PORT = 65432

with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    # s.sendall(b"Hello World")
    s.sendall(b"a")
    # s.send(b"hello world")
    data = s.recv(1024)

print(data)
print("Received {}".format(repr(data)))
