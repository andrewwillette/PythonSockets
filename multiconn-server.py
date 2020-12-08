#!/usr/local/bin/python3.8

import selectors
import socket
import types

host = "::1"
port = 65432
sel = selectors.DefaultSelector()

lsock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
lsock.bind((host,port))
lsock.listen()
print('listening on', (host, port))
lsock.setblocking(False)
sel.register(lsock,selectors.EVENT_READ, data=None)


def accept_wrapper(sock):
    conn, addr = sock.accept()
    print('accepted connection from', addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    print("accept_wrapper conn is ")
    print(conn)
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    print("service_connection mask is ")
    print(mask)
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
            print("data.outb is ")
            print(data.outb)
        else:
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('echoing', repr(data.outb), 'to', data.addr)
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]

while True:
    events = sel.select(timeout=None)
    print(events)
    for key, mask in events:
        if key.data is None:
            print('key.data is None')
            print(key)
            accept_wrapper(key.fileobj)
        else:
            print("key.data is not None")
            print(key)
            print(key.data)
            service_connection(key, mask)
