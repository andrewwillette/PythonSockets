#!/usr/local/bin/python3.8

import socket
import selectors

HOST = "::1"
PORT = 65432

sel = selectors.DefaultSelector()

lsock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
lsock.bind((host, port))
with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print("Connected by {}".format(addr))
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)
