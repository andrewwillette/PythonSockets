#!/usr/local/bin/python3.8

import sys
import selectors
import socket
import types

sel = selectors.DefaultSelector()


def accept_wrapper(sock):
    conn, addr = sock.accept()  # should be ready to read
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
    if mask & selectors.EVENT_READ:     # read data from the client socket
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
            print("data.outb is ")
            print(data.outb)
        else:
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:    # send data back to the socket that the server received it from
        if data.outb:
            print('echoing', repr(data.outb), 'to', data.addr)
            sent = sock.send(data.outb)
            data.outb = data.outb[sent:]


if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print('listening on', (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
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
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
