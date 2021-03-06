Following [Real Python tutorial](https://realpython.com/python-sockets/)
A majority of this readme is a manually copied version of that tutorial. Thank you Nathan Jennings, you are the man with a well spelled-out plan.

# Socket Programming in Python

Sockets and the socket API are used to send messages across a network. They provide a form of inter-process communication (IPC). The network can be a logical, local network to the computer, or one that's physically connected to an external network, with its own connections to other networks. The obvious example is the Internet, which you connect to via your ISP.

This tutorial has three different iterations of building a socket server and client with Python.

1. We'll start the tutorial by looking at a simple socket server and client.
2. Once you've seen the API and how things work in this initial example, we'll look at an improved version that handles multiple connections simultaneously.
3. Finally, we'll progress to building an example server and client that functions like a full-fledged socket application, complete with its own custom header and content.

By the end of this tutorial, you'll understand how to use the main functions and methods in Python's <code>socket</code> module to write your own client-server applications. This includes showing you how to use a custom class to send messages and data between endpoints that you can build upon and utilize for your own applications.

The examples in this tutorial use Python 3.6. [You can find the original source code on github](https://github.com/realpython/materials/tree/master/python-sockets-tutorial).

Networking and sockets are large subjects. Literal volumes have been written about them. If you're new to sockets or networking, it's completely normal if you feel overwhelmed with all of the terms and pieces.

Don't be discouraged though. I've written(copied) this tutorial for you. As we do with Python, we can learn a little bit at a time. Use your browser's bookmark feature and come back when you're ready for the next section.

## Background

Sockets have a long history. Their use [originated with ARPANET](https://en.wikipedia.org/wiki/Network_socket#History) in 1971 and later became an API in the Berkeley Software Distribution (BSD) operating system released in 1983 called [Berkeley sockets](https://en.wikipedia.org/wiki/Berkeley_sockets).

When the Internet took off in the 1990s with the World Wide Web, so did network programming. Web servers and browsers weren't the only applications taking the advantage of newly connected networks and using sockets. Client-server applications of all types and sizes came into widespread use.

Today, although the underlying protocols used by the socket API have evolved over the years, and we've seen new ones, the low-level API has remained the same.

The most common type of socket applications are client-server applications, where one side acts as the server and waits for connections from clients. This is the type of application that I'll be covering in this tutorial. More specifically, we'll look at the socket API for internet [Internet sockets](https://en.wikipedia.org/wiki/Berkeley_sockets), sometimes called Berkeley or BSD sockets. There are also [Unix domain sockets](https://en.wikipedia.org/wiki/Unix_domain_socket), which can only be used to communicate between the processes on the same host.

## Socket API Overview

Python's [socket module](https://docs.python.org/3/library/socket.html) provides an interface to the Berkeley sockets API. This is the module that we'll use and discuss in this tutorial.

The primary socket API functions and methods in this module are:

- <code>socket()</code>
- <code>bind()</code>
- <code>listen()</code>
- <code>accept()</code>
- <code>connect()</code>
- <code>connect_ex()</code>
- <code>send()</code>
- <code>recv()</code>
- <code>close()</code>

Python provides a convenient and consisten API that maps directly to these system calls, their C counterparts. We'll look at how these are used together in the next section.

As part of its standard library, Python also has classes that make using these low-level socket functions easier. Although it's not covered in this tutorial, see the [socketserver module](https://docs.python.org/3/library/socketserver.html), a framework for network servers. There are also many modules available that implement higher-level Internet protocols like HTTP and SMTP. For an overview, see [Internet Protocols and Support](https://docs.python.org/3/library/internet.html). 

## TCP Sockets

As you will see shortly, we will create a socket object using <code>socket.socket()</code> and specify the socket type as <code>socket.SOCK_STREAM</code>. When you do that, the default protocol that's used is the [Transmission Control Protocol](https://en.wikipedia.org/wiki/Transmission_Control_Protocol). This is a good default and probably what you want.

Why should you use TCP? The Transmission Control Protocol (TCP):

- **Is reliable**: packets dropped in the network are detected and retransmitted by the sender.
- **Has in-order data delivery**: data is read by your application in the order it was written by the sender.

In contrast, [User Datagram Protocol(UDP)](https://en.wikipedia.org/wiki/User_Datagram_Protocol) sockets created with <code>socket.SOCK_DGRAM</code> aren't reliable, and data read by the receiver can be out-of-order from the sender's writes.

Why is this important? Networks are a best-effort delivery system. There's no guarantee that your data will reach its destination or that you'll receive what's been sent to you.

Network devices (for example, routers and switches), have finite bandwidth available and their own inherent system limitations. They have CPUs, memory, buses, and interface packet buffers, just like our clients and servers. TCP relieves you from having to worry about [packet loss](https://en.wikipedia.org/wiki/Packet_loss), data arriving out-of-order, and many other things that invariably happen when you're communicating across a network.

In the diagram below, let's look at the sequence of socket API calls and data flow for TCP:

<pre>
            Server          Client

            socket
              | 
              V
             bind
              |                         Server creating listening socket
              V
            listen
              |
              V             socket
            accept            |
              |               V
              |<---------->connect      Establishing connection, three-way handshake
              |               |
              |               V
         -->recv<-----------send<--     Client sending data, server receiving data
         |     |              |   |
         |     V              V   |
         --send------------>recv---     server sending data, client receiving data
              |               |
              V               V
            recv<-----------close       client sending close message
              |
              V
            close
</pre>

The left hand-column represents the server. On the right-hand side is the client.

Starting in the top left-hand column, note the API calls the server makes to setup a "listening" socket:

- <code>socket()</code>
- <code>bind()</code>
- <code>listen()</code>
- <code>accept()</code>

A listening socket does just what it sounds like. It listens for connections from clients. When a client connects, the server calls <code>accept</code> to accept, or complete, the connection.

The client calls <code>connect()</code> to establish a connection to the server and initiate the three-way handshake. The handshake step is important since it ensures that each side of the connection is reachable in the network, in other words that the client can reach the server and vice-versa. It may be that only one host, client or server, can reach the other.

In the middle is the round-trip section, where data is exchanged between the client and server using calls to <code>send()</code> and <code>recv()</code>.

At the bottom, the client and server <code>close()</code> their respective sockets.

## Echo Client and Server

Now that you've seen an overview of the socket API and how the client and server communicate, let's create our first client and server. We will begin with a simple implementation. The server will simply echo whatever it receives back to the client.

### Echo Server

Here's the server, echo-server.py:

<pre>
#!/usr/bin/env python3

import socket

HOST = '127.0.0.1'      # standard loopback interface address (localhost)
PORT = 65432            # port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)
</pre>

Let's walk through each API call and see what's happening.

<code>socket.socket()</code> creates a socket object that supports the [context manager type](https://docs.python.org/3/reference/datamodel.html#context-managers), so you can use it in a [with statement](https://docs.python.org/3/reference/compound_stmts.html#with). There's no need to call s.close():

<pre>
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    pass    # use the socket object without calling s.close()
</pre>

The arguments passed to [socket()](https://docs.python.org/3/library/socket.html#socket.socket) specify the [address family](https://realpython.com/python-sockets/#socket-address-families) and socket type. AF_INET is the Internet address family for [IPv4](https://en.wikipedia.org/wiki/IPv4). SOCK_STREAM is the socket type for [TCP](https://realpython.com/python-sockets/#tcp-sockets), the protocol that will be used to transport our messages in the network.

<code>bind()</code> is used to associate the socket with a specific network interface and port number:
The multi-connection client and server example is definitely an improvement compared with where we started. However, let's take one more step and address the shortcomings of the previous multiconn example in a final implementation: the application client and server.

<pre>
HOST = '127.0.0.1'      # standard loopback interface address (localhost)
PORT = 65432            # port to listen on (non-privileged ports are > 1023)

# ...

s.bind((HOST, PORT))
</pre>

The values passed to <code>bind()</code> depend on the [address family](https://realpython.com/python-sockets/#socket-address-families) of the socket. In this example, we're using <code>socket.AF_INIT</code> (IPv4). So it expects a 2-tuple: <code>(host, port)</code>.

<code>host</code> can be a hostname, [IP address](https://realpython.com/python-ipaddress-module/), or empty string. If an IP address is used, <code>host</code> should be an IPv4-formatted address string. The IP address <code>127.0.0.1</code> is the standard IPv4 address for the [loopback](https://en.wikipedia.org/wiki/Localhost) interface, so only processes on the host will be able to connect to the server. If you pass an empty string, the server will accept connections on all available IPv4 interfaces.

<code>port</code> should be an integer from 1-65535 (0 is reserved). It's the [TCP port](https://en.wikipedia.org/wiki/Transmission_Control_Protocol#TCP_ports) number to accept connections on from clients. Some systems may require superuser privileges if the port is <code><1024</code>.

A note on using hostnames with <code>bind()</code>:

If you use a hostname in the host portion of IPv4/v6 socket address, the program may show a non-deterministic behavior, as Python uses the first address returned from the DNS resolution. The socket address will be resolved differently into an actual IPv4/v6 address, depending on the results from DNS resolution and/or the host configuration. For deterministic behavior use a numeric address in the host portion.

I'll discuss this later in "Using Hostnames", but it's worth mentioning here. For now, just understand that when using a hostname, you could see different results depending on what's returned from the name resolution process.

It could be anything. The first time you run your application, it might be the address <code>10.1.2.3</code>. The next time it's a different address, <code>192.168.0.1</code>. The third time, it could be <code>172.16.7.8</code>, and so on.

Continuing with the server example, <code>listen()</code> enables a server to <code>accept()</code> connections. It makes it a "listening" socket:

<pre>
s.listen()
conn, addr = s.accept()
</pre>

<code>listen()</code> has a <code>backlog</code> paramter. It specifies the number of unaccepted connections that the system will allow before refusing new connections. Starting in Python 3.5, it's optional. If not specified, a default <code>backlog</code> value is chosen.

If your server receives a lot of connection requests simultaneously, increasing the <code>backlog</code> value may help by setting the maximum length of the queue for pending connections. The maximum value is system dependent. For example, on Linux, see <code>/proc/sys/net/core/somaxconn</code>.

<code>accept()</code> [blocks](https://en.wikipedia.org/wiki/Berkeley_sockets#Blocking_and_non-blocking_mode) and waits for an incoming connection. When a client connects, it returns a new socket object representing the connection and a tuple holding the address of the client. The tuple will contain <code>(host, port)</code> for IPv4 connections or <code>(host, port, flowinfo, scopeid)</code> for IPv6. See [Socket Address Families](https://realpython.com/python-sockets/#socket-address-families) in the reference section for details on the tuple values.

One thing that's imperative to understand is that we now have a new socket object from <code>accept()</code>. This is important since it's the socket that you'll use to communicate with the client. It's distinct from the listening socket that the server is using to accept new connections:

<pre>
conn, addr = s.accept()
with conn:
    print('Connected by', addr)
    while True:
        data = conn.recv(1024)
        if not data:
            break
        conn.sendall(data)
</pre>

After getting the client socket object <code>conn</code> from <code>accept()</code>, an infinite <code>while</code> loop is used to loop over [blocking calls](https://realpython.com/python-sockets/#blocking-calls) to <code>conn.recv()</code>. This reads whatever data the client sends and echoes it back using <code>conn.sendall()</code>.

If <code>conn.recv()</code> returns an empty [bytes](https://docs.python.org/3/library/stdtypes.html#bytes-objects) object, b'', then the client closed the connection and the loop is terminated. The <code>with</code> statement is used with <code>conn</code> to automatically close the socket at the end of the block.

## Echo Client

Now let's look at the client, <code>echo-client.py</code>:

<pre>
#!/usr/bin/env python3

import socket

HOST = '127.0.0.1'      # the server's hostname or IP address
PORT = 65432            # the port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello World')
    data = s.recv(1024)

print('Received', repr(data))
</pre>

In comparison to the server, the client is pretty simple. It creates a socket object, connects to the server and calls <code>s.sendall()</code> to send its message. Lastly, it calls <code>s.recv()</code> to read the server's reply and then [prints it](https://realpython.com/python-print/).

## Running the Echo Client and Echo Server

Let's run the client and server to see how they behave and inspect what's happening.

Open a terminal or command prompt, navigate to the directory that contains your scripts, and run the server:

<pre>
$ ./echo-server.py
</pre>

Your terminal will appear to hang. That's because the server is [blocked](https://realpython.com/python-sockets/#blocking-calls)(suspended) in a call:

<pre>
conn, addr = s.accept()
</pre>

It's waiting for a client connection. Now open another terminal window or command prompt and run the client:

<pre>
$ ./echo-client.py
Received b'Hello, world'
</pre>

In the server window, you should see:

<pre>
$ ./echo-server.py
Connected by ('127.0.0.1', 64623)
</pre>

In the output above, the server printed the addr tuple returned from <code>s.accept()</code>. This is the client's IP address and TCP and port number. The port number, 64623, will most likely be different when you run it on your machine.

## Viewing Socket State

To see the current state of sockets on your host, use <code>netstat</code>. It's available by default macOS, Linux, and Windows.

Here's the netstat output from macOS after starting the server:

<pre>
$ netstat
Active Internet connections (including servers)
Proto      Recv-Q Send-Q  Local Address     Foreign Address     (state)
tcp6       0      0       ::1.65432         *.*                 LISTEN
</pre>

Notice that <code>Local Address</code> is <code>::1.65432</code>. If echo-server.py had used <code>HOST = ''</code> instead of <code>HOST = '127.0.0.1'</code>, netstat would show this:

<pre>
$ netstat
Active Internet connections (including servers)
Proto       Recv-Q  Send-Q  Local Address       Foreign Address     (state)
tcp4        0       0       *.65432             *.*                 LISTENING
</pre>

<code>Local Address</code> is <code>*.65432</code>, which means all available host interfaces that support the address family will be used to accept incoming connections. In this example, in the call to <code>socket()</code>, <code>socket.AF_INET</code> was used (IPv4). You can see this in the <code>Proto</code> column: <code>tcp4</code>.

I have trimmed the output above to show the echo server only. You'll likely see much more output, depending on the system you're running it on. The things to notice are the columns <code>Proto</code>, <code>Local Address</code> and <code>(state)</code>. In the last example above, netstat shows the echo server is using an IPv4 TCP socket (tcp4), on port 65432 on all interfaces (*.65432), and it's in the listening state (LISTEN).

Another way to see this, along with additional helpful information, is to use lsof (list open files). It's available by default on macOS and can be installed on Linux using your package manager, if it's not already:

<pre>
$ lsof -i -n
COMMAND     PID     USER        FD      TYPE        DEVICE      SIZE/OFF    NODE    NAME
Python      67982   andrew       3u     IPv6        0xecf272    0t0         TCP     *:6543 (LISTEN)
</pre>

<code>lsof</code> gives you the <code>COMMAND</code>, <code>PID</code>(process id) and <code>USER</code>(user id) of open Internet sockets when used with the <code>-i</code> option. Above is the echo server process.

<code>netstat</code> and <code>lsof</code> have a lot of options available and differ depending on the OS you're running them on. Check the man page or documentation for both. They're definitely worht spending a little time with and getting to know. You will be rewarded. On macOS and Linux, use <code>man netstat</code> and <code>man lsof</code>. For Windows, use <code>netstate /?</code>.

Here's a common error you will see when a connection attempt is made to a port with no listening socket:

<pre>
$ ./echo-client.py
Traceback (most recent call last):
    File "./echo-client.py", line 9, in <module>
        s.connect((HOST, PORT))
ConnectionRefusedError: [Errno 61] Connection refused
</pre>

Either the specified port number is wrong or the server isn't running. Or maybe there's a firewall in the path that's blocking the connection, which can be easy to forget about. You may also see the error <code>Connection timed out</code>. Get a firewall rule added that allows the client to connect to the TCP port!

There's a list of common [errors](https://realpython.com/python-sockets/#errors) in the reference section.

## Communication Breakdown

Let's take a closer look at how the client and server communicated with eachother :

<pre>
        ____________                    ________________
        |   Server |                    | Client       |
        |  Process |                    | Process      |
        |          |                    |              |
        |Listening |                    | Connect      |
        |on TCP    |                    | to 127.0.0.1 |
        |port 65432|                    | on TCP port  |
        -----------                     | 65432        |
             |                          ---------------
             |          loopback interface     |
             |          127.0.0.1 (::1)        |
             -----------------------------------

                            HOST
</pre>

When using the [loopback](https://en.wikipedia.org/wiki/Localhost) interface (IPv4 address 127.0.0.1 or IPv6 address ::1), data never leaves the host or touches the external network. In the diagram above, the loopback interface is contained inside the host. This represents the internal nature of the loopback interface and that connections and data that transit it are local to the host. This is why you'll also hear the loopback interface and IP address 127.0.0.1 or ::1 referred to as "localhost".

Applications use the loopback interface to communicate with other processes running on the host and for security and isolation from the external network. Since it's internal and accessible only from within the host, it's not exposed.

You can see this in action if you have an application server that uses its own private database. If it's not a database used by other servers, it's probably configured to listen for connections on the loopback interface only. If this is the case, other hosts on the network can't connect to it.

When you use an IP address other than <code>127.0.0.1</code> or <code>::1</code> in your applications, it's probably bound to an [Ethernet](https://en.wikipedia.org/wiki/Ethernet) interface that is connected to an external network. This is your gateway to other hosts outside of your "localhost" kingdom:
<pre>

       ____________________________               _____________________________
       |        Server Process     |              | Client Process            |
       |                           |              |                           |
       |        Listening on       |              | Connect to Server         |
       |        TCP port           |              | on TCP port               |  
       |        65432              |              | 65432                     |
       |                           |              |                           |
       | loopback       ethernet   |              | ethernet        loopback  |
       | interface      interface  |              | interface       interface |
       | lo0              eth0     |              | eth0            lo0       |
       -----------------------------              -----------------------------
                          |                          |
                          |--------------------------|

                Server Host                                 Client Host
</pre>

Be careful out there. It's a nasty, cruel world. Be sure to read the section [Using Hostnames](https://realpython.com/python-sockets/#using-hostnames) before venturing from the safe confines of "localhost." There is a security note that applies even if you are not using hostnames and using IP addresses only.

## Handling Multiple Connections

The echo server defintely has its limitations. The biggest being that it serves only one client and then exits. The echo client has this limitation too, but there's an additional problem. When the client makes the following call, it's possible that <code>s.recv()</code> will return only one byte, <code>b'H'</code> from <code>b'Hello, world'</code>:

<pre>
data = s.recv(1024)
</pre>

The <code>bufsize</code> argument of <code>1024</code> used above is the maximum amount of data to be received at once. It doesn't mean that <code>recv()</code> will return 1024 bytes.

<code>send()</code> also behaves this way. <code>send()</code> returns the number of bytes sent, which may be less than the size of the data passed in. You are responsible for checking this and calling <code>send()</code> as many times as needed to send all the data.

[Python offical socket.send() doc](https://docs.python.org/3/library/socket.html#socket.socket.send)...

`"Applications are responsible for checking that all data has been sent; if only some of the data was transmitted, the application needs to attempt delivery of the remaining data."`

We avoided having to do this by using <code>sendall()</code>:

[Python official socket.sendall() doc](https://docs.python.org/3/library/socket.html#socket.socket.sendall)

`"Unlike send(), this method continues to send data from bytes until either all data has been sent or an error occurs. None is returned on success."`

We have two problems at this point:

- How do we handle multiple connections concurrently?
- We need to call <code>send()</code> and <code>receive</code> until all data is sent or received.

What do we do? There are many approaches to [concurrency](https://realpython.com/python-concurrency/). More recently, a popular approach is to use [Asynchronous I/O](https://docs.python.org/3/library/asyncio.html). <code>asyncio</code> was introduced into the standard library in Python 3.4. The traditional choice is to use [threads](https://docs.python.org/3/library/threading.html).

The trouble with concurrency is it's hard to get right. There are many subtleties to consider and guard against. All it takes is for one of these to manifest itself and your application may suddenly fail in not-so-subtle ways.

I don't say this to scare you away from learning and using concurrent programming. If your application needs to scale, it's a necessity if you want to use more than one processor or one core. However, for this tutorial, we'll use something that's more traditional than threads and easier to reason about. We're going to use the granddaddy of system calls: <code>[select()](https://docs.python.org/3/library/selectors.html#selectors.BaseSelector.select)</code>.

<code>select()</code> allows you to check for I/O completion on more than one socket. So you can call select() to see which sockets have I/O ready for reading and/or writing. But this is Python, so there's more. We're going to use [selectors](https://docs.python.org/3/library/selectors.html) module in the standard library so the most efficient implementation is used, regardless of the operating system we happen to be running on:

From the [selectors documentation](https://docs.python.org/3/library/selectors.html)...

`"This module allows high-level and efficient I/O multiplexing, built upon the select module primitives. Users are encouraged to use this module instead, unless they want precise control over the OS-level primitives used."`

Even though, by using <code>select()</code>, we are not able to run concurrently, depending on your workload, this approach may still be plenty fast. It depends on what your application needs to do when it services a request and the number of clients it needs to support.

<code>[asyncio](https://docs.python.org/3/library/asyncio.html)</code> uses single-threaded cooperative multitasking and an event loop to manage tasks. With <code>select()</code>, we will be writing our own version of an event loop, albeit more simply and synchronously. When using multiple threads, even though you have concurrency, we currently have to use the [GIL](https://realpython.com/python-gil/) with [CPython and PyPy](https://wiki.python.org/moin/GlobalInterpreterLock). This effectively limits the amount of work we can do in parallel anyway.

I say all of this to explain that using <code>select()</code> may be a perfectly fine choice. Don't feel like you have to use <code>asyncio</code>, threads, or the latest asynchronous library. Typically, in a network application, your application is I/O bound: it could be waiting on the local network, endpoints on the other side of the network, on a disk, and so forth.

If you're getting requests from clients that initiate CPU bound work, look at the [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html) module. It contains the class [ProcessPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor) that uses a pool of processes to execute calls asynchronously.

If you use multiple processes, the operating system is able to schedule your Python code to run in parallel on multiple processors or cores, without the GIL. For ideas and inspiration, see the PyCon talk [John Reese - Thinking Outside the GIL with AsyncIO and Multiprocessing - PyCon 2018](https://www.youtube.com/watch?v=0kXaLh8Fz3k).

In the next section, we will look at examples of a server and client that address these problems. They use <code>select()</code> to handle multiple connections simultaneously and call <code>send()</code> and <code>recv()</code> as many times as needed.

## Multi-Connection Client and Server

In the next two sections, we will create a server and client that handles multiple connections using a <code>selector</code> object created from the [selectors](https://docs.python.org/3/library/selectors.html) module.

### Multi-Connection Server

First, let's look at the multi-connection server, <code>multiconn-server.py</code>. Here's the first part that sets up the listening socket:

<pre>
import selectors
sel = selectors.DefaultSelector()
# ...
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print('listening on', (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)
</pre>

The biggest difference between this server and the echo server is the call to <code>lsock.setblocking(False)</code> to configure the socket in non-blocking mode. Calls made to this socket will no longer [block](https://realpython.com/python-sockets/#blocking-calls). When it's used with <code>sel.select()</code>, as you'll see below, we can wait for events on one or more sockets and then read and write data when it's ready.

<code>sel.register()</code> registers the socket to be monitored with <code>sel.select()</code> for the events you're interested in. For the listening socket, we want read events: <code>selectors.EVENT_READ</code>.

<code>data</code> is used to store whatever arbitrary data you'd like along with the socket. It's returned with <code>select()</code> returns. We will use <code>data</code> to keep track of what's been sent and received on the socket.

Next is the event loop:

<pre>
import selectors
sel = selectors.DefaultSelect()

# ...

while True:
    events = sel.select(timeout=None)
    for key, mask in events:
        if key.data is None:
            accept_wrapper(key.fileobj)
        else:
            service_connection(key, mask)
</pre>

<code>[sel.select(timeout=None)](https://docs.python.org/3/library/selectors.html#selectors.BaseSelector.select)</code> [blocks](https://realpython.com/python-sockets/#blocking-calls) until there are sockets ready for I/O. It returns a list of <code>(key, events)</code> tuples, one for each socket. <code>key</code> is a [SelectorKey](https://docs.python.org/3/library/selectors.html#selectors.SelectorKey) <code>namedtuple</code> that contains a <code>fileobj</code> attribute. <code>key.fileobj</code> is the socket object, and <code>mask</code> is an event mask of the operations that are ready.

If <code>key.data</code> is <code>None</code>, then we know it's from the listening socket and we need to <code>accept()</code> the connection. We will call our own <code>accept()</code> wrapper function to get the new socket object and register it with the selector. We will look at it in a moment.

If <code>key.data</code> is not <code>None</code>, then we know it's a client socket that's already been accepted, and we need to service it. <code>service_connection()</code> is then called and passed <code>key</code> and <code>mask</code>, which contains everything we need to operate on the socket.

Let's look at what our <code>accept_wrapper()</code> function does:

<pre>
def accept_wrapper(sock):
    conn, addr = sock.accept()      # should be ready to read
    print('accepted connection from', addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
</pre>

Since the listening socket was registered for the event <code>selectors.EVENT_READ</code>, it should be ready to read. We call <code>sock.accept()</code> and then immediately call <code>conn.setblocking(False)</code> to put the socket in non-blocking mode.

Remember, this is the main objective in this version of the server since we don't want it to [block](https://realpython.com/python-sockets/#blocking-calls). If it blocks, then the entire server is stalled until it returns. Which means other sockets are left waiting.This is the dreaded "hang" state that you don't want your server to be in.

Next, we create an object to hold the data we want included along with the socket using the class <code>types.SimpleNamespace</code>. Since we want to know when the client connection is ready for reading and writing, both of those events are set using the following:

<pre>
events = selectors.EVENT_READ | selectors.EVENT_WRITE
</pre>

The events mask, socket, and data objects are then passed to sel.register().

Now let's look at <code>service_connection()</code> to see how a client connection is handled when it's ready:

<pre>
def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)     # should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            print('closing connection to', data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print('echoing', repr(data.outb), 'to', data.addr)
            sent = sock.send(data.outb)     # should be ready to write
            data.outb = data.outb[sent:]
</pre>

This is the heart of the simple multi-connection server. <code>key</code> is the <code>namedtuple</code> returned from <code>select()</code> that contains the socket object (<code>fileobj</code>) and <code>data</code> object. <code>mask</code> contains the events that are ready.

If the socket is ready for reading, then <code>mask</code> & <code>selectors.EVENT_READ</code> is true(Note: this makes no f'in sense at all, <code>selectors.EVENT_READ</code> is a reference to the <code>selectors</code> module. The hell is it have state?), and <code>sock.recv()</code> is called. Any data that is read is appended to <code>data.outb</code> so it can be sent later.

Note the <code>else:</code> block if no data is received:

<pre>
if recv_data:
    data.outb += recv_data
else:
    print('closing connection to', data.addr)
    sel.unregister(sock)
    sock.close()
</pre>

This means that the client has closed their socket, so the server should too. But don't forget to first call <code>sel.unregister()</code> so it's no longer monitored by <code>select()</code>.

When the socket is ready for writing, which should always be the case for a health socket, any received data stored in <code>data.outb</code> is echoed to the client using <code>sock.send()</code>. The bytes sent are then removed from the send buffer:

<pre>
data.outb = data.outb[sent:]
</pre>

### Multi-Connection Client

Now let's look at the multi-connection client, <code>multiconn-client.py</code>. It is very similar to the server, but instead of listening for connections, it starts by initiating connections via <code>start_connections()</code>:

<pre>
messages = [b'Message 1 from client.', b'Message 2 from client.']


def start_connections(host, port, num_conns):
    server_addr = (host, port)
    for i in range(0, num_conns):
        connid = i + 1
        print('starting connection', connid, 'to', server_addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(connid=connid,
                                    msg_total=sum(len(m) for m in messages),
                                    recv_total=0,
                                    messages=list(messages),
                                    outb=b'')
        sel.register(sock, events, data=data)
</pre>

<code>num_conns</code> is read from the command-line, which is the number of connections to create to the server. Just like the server, each socket is set to non-blocking mode.

<code>connect_ex()</code> is used instead of <code>connect()</code> since <code>connect</code> would immediately raise a <code>BlockingIOError</code> exception. <code>connect_ex()</code> initially returns an error indicator, <code>errno.EINPROGRESS</code>, instead of raising an exception while the connection is in progress. Once the connection is completed, the socket is ready for reading and writing and is returned as such by <code>select()</code>.

After the socket is setup, the data we want stored with the socket is created using the class <code>types.SimpleNamespace</code>. The messages the client will send to the server are copied using <code>list(messages)</code> since each connection will call <code>socket.send()</code> and modify the list. Everything needed to keep track of what the client needs to send, has sent and received, and the total number of bytes in the messages is stored in the object data.

Let's look at the <code>service_connection()</code>. It's fundamentally the same as the server:

<pre>
def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)     # should be ready to read
        if recv_data:
            print('received', repr(recv_data), 'from connection', data.connid)
            data.recv_total += len(recv_data)
        if not recv_data or data.recv_total == data.msg_total:
            print('closing connection', data.connid)
            sel.unregister(sock)
            sock.close()
        if mask & selectors.EVENT_WRITE:
            if not data.outb and data.messages:
                data.outb = data.messages.pop(0)
            if data.outb:
                print('sending', repr(data.outb), 'to connection', data.connid)
                sent = sock.send(data.outb)     # should be ready to write
                data.outb = data.outb[sent:]
</pre>

There's one important difference. It keeps track of the number of bytes it's received from the server so it can close its side of the connection. When the server detects this, it closes its side of the connection too.

Note that by doing this, the server depends on the client being well-behaved: the server expects the client to close its side of the connection when it's done sending messages. If the client doesn't close, the server will leave the connection open. In a real application, you may want to guard against this in your server and prevent client connections from accumulating if they don't send a request from a certain amount of time.

### Running the Multi-Connection Client and Server

Now let's run the <code>multiconn-server.py</code> and <code>multiconn-client.py</code>. They both use [command-line arguments](https://realpython.com/python-command-line-arguments/). You can run them without arguments to see the options.

For the server, pass a <code>host</code> and <code>port</code> number:

<pre>
$ ./multiconn-server.py
usage: ./multiconn-server.py <host> <port>
</pre>

For the client, also pass the number of connections to create to the server, <code>num_connections</code>:

<pre>
$ ./multiconn-client.py
usage: ./multiconn-client.py <host> <port> <num_connections>
</pre>

Below is the server output when listening on the loopback interface on port 65432:

<pre>
$ ./multiconn-server.py 127.0.0.1 65432
listening on ('127.0.0.1', 65432)
accepted connection from ('127.0.0.1', 61354)
accepted connection from ('127.0.0.1', 61355)
echoing b'Message 1 from client.Message 2 from client.' to ('127.0.0.1', 61354)
echoing b'Message 1 from client.Message 2 from client.' to ('127.0.0.1', 61355)
closing connection to ('127.0.0.1', 61354)
closing connection to ('127.0.0.1', 61355)
</pre>

Below is the client output when it creates two connections to the server above:

<pre>
$ ./multiconn-client.py 127.0.0.1 65432 2
starting connection 1 to ('127.0.0.1', 65432)
starting connection 2 to ('127.0.0.1', 65432)
sending b'Message 1 from client.' to connection 1
sending b'Message 2 from client.' to connection 1
sending b'Message 1 from client.' to connection 2
sending b'Message 2 from client.' to connection 2
received b'Message 1 from client.Message 2 from client.' from connection 1
closing connection 1
received b'Message 1 from client.Message 2 from client.' from connection 2
closing connection 2
</pre>

## Application Client and Server

The multi-connection client and server example is defintely an improvement compared with where we started. However, let's take one more step and address the shortcomings of the previous "multiconn" example in a final implementation: the application client and server.

We want a client and server that handles errors appropriately so other connections aren't affected. Obviously, our client or server shouldn't come crashing down in a ball of fury if an exception isn't caught. This is something we haven't discussed up until now. I've intentionally left out error handling for brevity and clarity in the examples.

Now that you're familiar with the basic API, non-blocking sockets, and <code>select()</code>, we can add some error handling and discuss the "elephant in the room" that I've kept hidden from you behind that large curtain over there. Yes, I'm talking about the custom class I mentioned way back in the introduction. I knew you wouldn't forget.

First, let's address the errors:

[From Pythons official socket documentation](https://docs.python.org/3/library/socket.html)...

`"All errors raise exceptions. The normal exceptions for invalid argument types and out-of-memory conditions can be raised; starting from Python 3.3, errors related to socket or address semantics raise OSError or one of its subclasses.`

We need to catch <code>OSError</code>. Another thing I haven't mentioned in relation to errors is timeouts. You'll see them discussed in many places in the documentation. Timeouts happen and are a "normal" error. Hosts and routers are rebooted, switch ports go bad, cables go bad, cables get unplugged, you name it. You should be prepared for these and other errors and handle them in your code.

What about the "elephant in the room?" As hinted by the socket type <code>socket.SOCK_STREAM</code>, when using TCP, you're reading from a continuous stream of bytes. It's like reading from a file on disk, but instead you're reading bytes from the network.

However, unlike reading a file, there's no <code>[f.seek()](https://docs.python.org/3/tutorial/inputoutput.html#methods-of-file-objects)</code>. In other words, you can't reposition the socket pointer, if there was one, and move randomly around the data reading whatever, whenever you'd like.

When bytes arrive at your socket, there are network buffers involved. Once you've read them, they need to be saved somewhere. Calling <code>recv()</code> again reads the next stream of bytes available from the socket.

What this means is that you'll be reading from the socket in chunks. You need to call <code>recv()</code> and save the data in a buffer until you've read enough bytes to have a complete message that makes sense to your application.

It's up to you to define and keep track of where the message boundaries are. As far as the TCP socket is concerned, it's just sending and receiving raw bytes to and from the network. It knows nothing about what those raw bytes mean.

This brings us to defining an application-layer protocol. What's an application-layer protocol? Put simply, your application will send and receive messages. These messages are your application's protocol.

In other words, the length and format you choose for these messages define the semantics and behavior of your application. This is directly related to what I explained in the previous paragraph regarding reading bytes from the socket. When you're reading bytes with <code>recv()</code>, you need to keep up with how many bytes were read and figure out where the message boundaries are.

How is this done? One way is to always send fixed-length messages. If they're always the same size, then it's easy. When you've read that number of bytes into a buffer, then you know you have one complete message.

However, using fixed-length messages is inefficient for small messages where you'd need to use padding to fill them out. Also, you're still left with the problem of what to do about data that doesn't fit into one message.

In this tutorial, we'll take a generic approach. An approach that's used by many protocols, including HTTP. We'll prefix messages with a header that includes the content length as well as any other fields we need. By doing this, we'll only need to keep up with the header. Once we've read the header, we can process it to determine the length of the message's content and then read that number of bytes to consume it.

We'll implement this by creating a custom class that can send and receive messages that contain text or binary data. You can improve and extend it for your own applications. The most important thing is that you'll be able to see an example of how this is done.

I need to mention something regarding sockets and bytes that may affect you. As we talked about earlier, when sending and receiving data via sockets, you're sending and receiving raw bytes.

If you receive data and want to use it in a context where it's interpreted as multiple bytes, for example a 4-byte integer, you'll need to take into account that it could be in a format that's not native to your machine's CPU. The client or server on the other end could have a CPU that uses a different byte order than your own. If this is the case, you'll need to convert it to your host's native byte order before using it.

This byte order is referred to as a CPU's [endianness](https://en.wikipedia.org/wiki/Endianness). See [Byte Endianness](https://realpython.com/python-sockets/#byte-endianness) in the reference section for details. We'll avoid this issue by taking advantage of [Unicode](https://realpython.com/python-encodings-guide/) for our message header and using the encoding UTF-8. Since UTF-8 uses an 8-bit encoding, there are no byte ordering issues.

You can find an explanation in Python's [Encodings and Unicode](https://docs.python.org/3/library/codecs.html#encodings-and-unicode) documentation. Note that this applies to the text header only. We'll use an explicit type and encoding defined in the header for the content that's being sent, the message payload. This will allow us to transfer any data we'd like (text or binary), in any format.

You can easily determine the byte order of your machine by using sys.byteorder. For example, on my Intel laptop, this happens:

<pre>
python3 -c 'import sys; print(repr(sys.byteorder))'
'little'
</pre>

If I run this in a virtual machine that [emulates](https://www.qemu.org/) a big-endian CPU (PowerPC), then this happens:

<pre>
python3 -c 'import sys; print(repr(sys.byteorder))'
'big'
</pre>

In this example application, our application-layer protocol defines the header as Unicode text with a UTF-8 encoding. For the actual content in the message, the message payload, you'll have to swap the byte order manually if needed. 

This will depend on your application and whether or not it needs to process multi-byte binary data from a machine with different endianness. You can help your client or server implement binary support by adding additional headers and using them to pass parameters, similar to HTTP.

Don't worry if this doesn't make sense yet. In the next section, you'll see how all of this works and fits together.

## Application Protocol Header

Let's fully define the protocol header. The protocol header is:
- Variable length text
- Unicode with the encoding UTF-8
- A Python dictionary serialized using [JSON](https://realpython.com/python-json/)

The required headers, or sub-headers, in the protocol header's dictionary are as follows:

|Name|Description|
|------|------|
|byteorder|The byte order of the machine (uses <code>sys.byteorder</code>). This may not be required for your application.|
|content-length|The length of the content in bytes|
|content-type|The type of content in the payload, for example, <code>text/json</code> or <code>binary/my-binary-type</code>.|
|content-encoding|The encoding used by the content, for example, <code>utf-8</code> for Unicode text or <code>binary</code> for binary data.|

These headers inform the receiver about the content in the payload of the message. This allows you to send arbitrary data while providing enough information so the content can be decoded and interpreted correctly by the receiver. Since the headers are in a dictionary, it's easy to add additional headers by inserting key/value pairs as needed.

## Sending an Application Message

There's still a bit of a problem. We have a variable-length header, which is nice and flexible, but how do you know the length of the header when reading it with <code>recv()</code>?

When we previously talked about using <code>recv()</code> and message boundaries, I mentioned that fixed-length headers can be inefficient. That's true, but we're going to use a small, 2-byte, fixed-length header to prefix the JSON header that contains its length.

You can think of this as a hybrid approach to sending messages. In effect, we're bootstrapping the message receive process by sending the length of the header first. This makes it easy for our receiver to deconstruct the message.

To give you a better idea of the format, let's look at a message in its entirety:

<pre>
                            MESSAGE
           ____________________________________________
           | Fixed Length Header                      |
           | Type: 2 byte integer                     |
           | Byte Order: network (big-endian)         |
           ____________________________________________
           |  Variable-length JSON Header             |
           | Type: Unicode text                       |
           | Encoding: UTF-8                          |
           | Length: specified by fixed-length header |
           ____________________________________________
           | Variable-length Content                  |
           | Type: specified in JSON header           |
           | Encoding: specified in JSON header       |
           | Length: specified in JSON Header         |
           --------------------------------------------
</pre>

A message starts with a fixed-length header of 2-bytes that's an integer in network byte order. This is the length of the next header, the variable-length JSON header. Once we've read 2 bytes with <code>recv()</code>, then we know we can process the 2 bytes as an integer and then read that number of bytes before decoding the UTF-8 JSON header.

The [JSON header](https://realpython.com/python-sockets/#application-protocol-header) contains a dictionary of additional headers. One of those is content-length, which is the number of bytes of the message's content (not including the JSON header). Once we've called <code>recv()</code> and read content-length bytes, we've reached a message boundary and read an entire message.

## Application Message Class
Finally the payoff! Let's look at the <code>Message</code> class and see how it's used with <code>select()</code> when read and write events happen on the socket.

For this example application, I had to come up with an idea for what types of messages the client and server would use. We're far beyond toy echo clients and servers at this point.

To keep things simple and still demonstrate how things would work in a real application, I created an application protocol that implements a basic search feature. The client sends a search request and the server does a lookup for a match. If the request sent by the client isn't recognized as a search, the server assumes it's a binary request and returns a binary response.

After reading the following sections, running the examples, and experimenting with the code, you'll see how things work. You can then use the <code>Message</code> class as a starting point and modify it for your own use.

We're really not that far off from the "multiconn" client and server example. The event loop code stays the same in <code>app-client.py</code> and <code>app-server.py</code>. What I've done is move the message code into a class named <code>Message</code> and added methods to support reading, writing, and processing of the headers and content. This is a great example for using a class.

As we discussed before and you'll see below, working with sockets involves keeping state. By using a class, we keep all of the state, data, and code bundled together in an organized unit. An instance of the class is created for each socket in the client and server when a connection is started or accepted.

The class is mostly the same for both the client and the server for the wrapper and utility methods. They start with an underscore, like <code>Message._json_encode()</code>. These methods simplify working with the class. They help other methods by allowing them to stay shorter and support the DRY principle.

The server's <code>Message</code> class works in essentially the same way as the client's and vice-versa. The difference being that the client initiates the connection and sends a request message, followed by processing the server's response message. Conversely, the server waits for a connection, processes the client's request message, and then sends a response message.

It looks like this:

|Step|Endpoint|Action/Message Content|
|----|--------|----------------------|
|1|Client|Sends a <code>Message</code> containing request content|
|2|Server|Receives and processes client request <code>Message</code>|
|3|Server|Sends a <code>Message</code> containing response content|
|4|Client|Receives and processes server response <code>Message</code>|

Here's the file and code layout:

|Application|File|Code|
|-----------|----|----|
|Server|app-server.py|The server's main script|
|Server|libserver.py|The server's <code>Message</code> class|
|Client|app-client.py|The client's main script|
|Client|libclient.py|The client's <code>Message</code> class|

### Message Entry Point

I'd like to discuss how the <code>Message</code> class works by first mentioning an aspect of its design that wasn't immediately obvious to me. Only after refactoring it at least five times did I arrive at what it is currently. Why? Managing state.

After a Message object is created, it's associated with a socket that's monitored for events using <code>selector.register()</code>:

<pre>
message = libserver.Message(sel, conn, addr)
sel.register(conn, selectors.EVENT_READ, data=message)
</pre>

When events are ready on the socket, they're returned by <code>selector.select()</code>. We can then get a reference back to the message object using the data attribute on the key object and call a method in Message:

<pre>
while True:
    events = sel.select(timeout=None)
    for key, mask in events:
        # ...
        message = key.data
        message.process_events(mask)
</pre>

Looking at the event loop above, you'll see that <code>sel.select()</code> is in the driver's seat. It's blocking, waiting at the top of the loop for events. It's responsible for waking up when read and write events are ready to be processed on the socket. Which means, indirectly, it's also responsible for calling the method <code>process_events()</code>. This is what I mean when I say the method <code>process_events()</code> is the entry point.

Let's see what the <code>process_events()</code> method does:

<pre>
def process_events(self, mask):
    if mask & selectors.EVENT_READ:
        self.read()
    if mask & selectors.EVENT_WRITE:
        self.write()
</pre>

That's good: <code>process_events()</code> is simple. It can only do two things: call <code>read()</code> and <code>write()</code>.

This brings us back to managing state. After a few refactorings, I decided that if another method depended on state variables having a certain value, then they would only be called from <code>read()</code> and <code>write()</code>. This keeps the logic as simple as possible as events come in on the socket for processing.

This may seem obvious, but the first few iterations of the class were a mix of some methods that checked the current state and, depending on their value, called other methods to process data outside <code>read()</code> or <code>write()</code>. In the end, this proved too complex to manage and keep up with.

You should defintely modify the class to suit your own needs so it works best for you, but I'd recommend that you keep the state checks and the calls to methods that depend on that state to the <code>read()</code> and <code>write()</code> methods if possible.

Let's look at <code>read()</code>. This is the server's version, but the client's is the same. It just uses a different method name, <code>process_response()</code> instead of <code>process_request()</code>:

<pre>
def read(self):
    self._read()

    if self._jsonheader_len is None:
        self.process_protoheader()

    if self._jsonheader_len is not None:
        if self.jsonheader is None:
            self.process_jsonheader()
</pre>

The <code>_read()</code> method is called first. It calls <code>socket.recv()</code> to read data from the socket and store it in a receive buffer. Remember that when <code>socket.recv()</code> is called, all of the data that makes up a complete message may not have arrived yet. <code>socket.recv()</code> may need to be called again. This is why there are state checks for each part of the message before calling the appropriate method to process it.

Before a method processes its part of the message, it first checks to make sure enough bytes have been read into the receive buffer. If there are, it processes its respective bytes, removes them from the buffer and writes its output to a variable that's used by the next processing stage. Since there are three components to a message, there are three state checks and process method calls:

|Message Component|Method|Output|
|-----------------|------|------|
|Fixed-length-header|process_protoheader()|self._jsonheader_len|
|JSON header|process_jsonheader()|self.jsonheader|
|Content|process_request()|self.request|

Next, let's look at <code>write()</code>. This is the server's version:

<pre>
def write(self):
    if self.request:
        if not self.response_created:
            self.create_response()

    self._write()
</pre>

<code>write()</code> checks first for a request. If one exists and a response hasn't been created, <code>create_response()</code> is called. <code>create_response()</code> sets the state variable <code>response_created</code> and writes the response to the send buffer.

The <code>_write()</code> method calls <code>socket.send()</code> if there's data in the send buffer.

Remember that when <code>socket.send()</code> is called, all of the data in the send buffer may not have been queued for transmission. The network buffers for the socket may be full, and <code>socket.send()</code> may need to be called again. This is why there are state checks. <code>create_response()</code> should only be called once, but it's expected that <code>_write()</code> will need to be called multiple times.

The client version of <code>write()</code> is similar:

<pre>
def write(self):
    if not self._request_queued:
        self.queue_request()
    self._write()
    if self._request_queued:
        if not self._send_buffer:
            # set selector to listen for read events, we're done writing.
            self._set_selector_events_mask('r') 
</pre>

Since the client initiates a connection to the server and sends a request first, the state variable <code>_request_queued</code> is checked. If a request hasn't been queued, it calls <code>queue_request()</code>. <code>queue_request()</code> creates the request and writes it to the send buffer. It also sets the state variable <code>_request_queued</code> so it's only called once.

Just like the server, <code>_write()</code> calls <code>socket.send()</code> if there's data in the send buffer.

The notable difference in the client's version of <code>write()</code> is the last check to see if the request has been queued. This will be explained more in the section Client Main Script, but the reason for this is to tell <code>selector.select()</code> to stop monitoring the socket for write events. If the request has been queued and the send buffer is empty, then we're done writing and we're only interested in read events. There's no reason to be notified that the socket is writeable.

I'll wrap up this section by leaving you with one thought. The main purpose of this section was to explain that <code>selector.select()</code> is calling in the Message class via the method <code>process_event()</code> and to describe how state is managed.

This is important because <code>process_events()</code> will be called many times over the life of the connection. Therefore, make sure that any methods that should only be called once are either checking a state variable themselves, or the state variable set by the method is checked by the caller.

### Server Main Script

In the server's main script <code>app-server.py</code>, arguments aree read from the command line specify the interface and port to listen on:

<pre>
$ ./app-server.py
usage: ./app-server.py <host> <port>
</pre>

For example, to listen oono the loopback interface on port 65432, enter:

<pre>
$ ./app-server.py 127.0.0.1 65432
listening on ('127.0.0.1', 65432)
</pre>

Use an empty string for <code><host></code> to listen on all interfaces.

After creating the socket, a call is made to <code>socket.setsockopt()</code> with the option <code>socket.SO_REUSEADDR</code>:

<pre>
# avoid bind() exception: OSError: [Errno 48] Address already in use
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
</pre>

Setting this socket option avoids the error <code>Address already in use</code>. You'll see this when starting the server and a previously used TCP socket on the same port has connections in the <code>[TIME_WAIT](http://www.serverframework.com/asynchronousevents/2011/01/time-wait-and-its-design-implications-for-protocols-and-scalable-servers.html)</code> state.

For example, if the server actively closed a connection, it will remain in the <code>TIME_WAIT</code> state for two minutes or more, depending on the operating system. If you try to start the server again before the <code>TIME_WAIT</code> state expires, you'll get an <code>OSError</code> exception of <code>Address already in use</code>. This is a safeguard to make sure that any delayed packets in the network aren't delivered to the wrong application.

The event loop catches any errors so the server can stay up and continue to run:

<pre>
while True:
    events = sel.select(timeout=None)
    for key, mask in events:
        if key.data is None:
            accept_wrapper(key.fileobj)
        else:
            message = key.data
            try:
                message.process_events(mask)
            except Exception:
                print('main: error: exception for',
                    f'{message.addr}:\n{traceback.format_exc()}')
                message.close()
</pre>

When a client connection is accepted, a <code>Message</code> object is created:

<pre>
def accept_wrapper(sock):
    conn, addr = sock.accept()
    print('accepted connection from', addr)
    conn.setblocking(False)
    message = libserver.Message(sel, conn, addr)
    sel.register(conn, selectors.EVENT_READ, data=message)
</pre>

The <code>Message</code> object is associated with the socket in the call to <code>sel.register()</code> and is initially set to be monitored for read events only. Once the request has been read, we'll modify it to listen for write events only.

An advantage of taking this approach in the server is that in most cases, when a socket is healthy and there are no network issues, it will always be writable.

If we told <code>sel.register()</code> to also monitor <code>EVENT_WRITE</code>, the event loop would immediately wakeup and notify us that this is the case. However, at this point, there's no reason to wakeup and call <code>send()</code> on the socket. There's no response to send since a request hasn't been processed yet. This would consume and waste valuable CPU cycles.

### Server Message Class

In the section [Message Entry Point](https://realpython.com/python-sockets/#message-entry-point), we looked at how the <code>Message</code> object was called into action when socket events were ready via <code>process_events()</code>. Now let's look at what happens as data is read on the socket and a component, or piece, of the message is ready to be processed by the server.

The server's message class is in <code>libserver.py</code>.

The methods appear in the class in the order in which processing takes place for a message.

When the server has read at least 2 bytes, the fixed-length header can be processed:

<pre>
def process_protoheader(self):
    hdrlen=2
    if len(self._recv_buffer) >= hdrlen:
        self._jsonheader_len = struct.unpack('>H', self._recv_buffer[:hdrlen])[0]
        self._recv_buffer = self._recv_buffer[hdrlen:]
</pre>

The fixed-length header is a 2-byte integer in network (big-endian) byte order that contains the length of the JSON header. <code>[struct.unpack()](https://docs.python.org/3/library/struct.html)</code> is used to read the value, decode it, and store it in self._jsonheader_len. After processing the piece of the message it’s responsible for, process_protoheader() removes it from the receive buffer.

Just like the fixed-length header, when there’s enough data in the receive buffer to contain the JSON header, it can be processed as well:

<pre>
def process_jsonheader(self):
    hdrlen = self._jsonheader_len
    if len(self._recv_buffer) >= hdrlen:
        self.jsonheader = self._json_decode(self._recv_buffer[:hdrlen], 'utf-8')
        self._recv_buffer = self._recv_buffer[hdrlen:]
        for reqhdr in ('byteorder', 'content-length', 'content-type', 'content-encoding'):
            if reqhdr not in self.jsonheader:
                raise ValueError(f'Missing required header "{reqhdr}".')
</pre>

The method <code>self._json_decode()</code> is called to decode and deserialize the JSON header into a dictionary. Since the JSON header is defined as Unicode with a UTF-8 encoding, <code>utf-8</code> is hardcoded in the call. The result is saved to <code>self.jsonheader</code>. After processing the piece of the message it's responsible for, <code>process_jsonheader()</code> removes it from the receive buffer.

Next is the actual content, or payload, of the message. It's described by the JSON header in <code>self.jsonheader</code>. When content-length bytes are available in the receive buffer, the request can be processed:

<pre>
def process_request(self):
    content_len = self.jsonheader['content-length']
    if not len(self._recv_buffer) >= content_len:
        return
    data = self._recv_buffer[:content_len]
    self._recv_buffer = self._recv_buffer[content_len:]
    if self.jsonheader['content-type'] == 'text/json':
        encoding = self.jsonheader['content-encoding']
        self.request = self._json_decode(data, encoding)
        print('received request', repr(self.request), 'from', self.addr)
    else:
        # binary or unknown content-type
        self.request = data
        print(f'received {self.jsonheader["content-type"]} request from', self.addr)
    # set selector to listen for write events, we're done reading.
    self._set_selector_events_mask('w')
</pre>

After saving the message content to the <code>data</code> variable, <code>process_request()</code> removes it from the receive buffer. Then, if the content type is JSON, it decodes and deserializes it. If it's not, for this example application, it assumes it's a binary request and simply prints the content type.

The last thing <code>process_request()</code> does is modify the selector to monitor write events only. In the server's main script, <code>app-server.py</code>, the socket is initially set to monitor read events only. Now that the request has been fully processed, we're no longer interested in reading.

A response can now be created and written to the socket. When the socket is writable, <code>create_response()</code> is called from <code>write()</code>:

<pre>
def create_response(self):
    if self.jsonheader['content-type'] == 'text/json'
        response = self._create_response_json_content()
    else:
        # binary or unknown content-type
        response = self._create_response_binary_content()
    message = self._create_message(**response)
    self.response_created = True
    self._send_buffer += message
</pre>

A response is created by calling other methods, depending on the content type. In this example application, a simple dictionary lookup is done for JSON requests when <code>action == 'search'</code>. You can define other methods for your applications that get called here.

After creating the response message, the state variable <code>self.response_created</code> is set so <code>write()</code> doesn't call <code>create_response()</code> again. Finally, the response is appended to the send buffer. This is seen by and sent via <code>_write()</code>.

One tricky bit to figure out was how to close the connection after the response is written. I put the call to <code>close()</code> in the method <code>_write()</code>:

<pre>
def _write(self):
    if self._send_buffer:
        print('sending', repr(self._send_buffer), 'to', self.addr)
        try:
            # should be ready to write
            sent = self.sock.send(self._send_buffer)
        except BlockingIOError:
            # resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            self._send_buffer = self._send_buffer[sent:]
            if sent and not self._send_buffer:
                self.close()
</pre>

Although it's somewhat "hidden", I think it's an acceptable trade-off give that the <code>Message</code> class only handles one message per connection. After the response is written, there's nothing left for the server to do. It's completed its work.

### Client Main Script

In the client's main script <code>app-client.py</code>, arguments are read from the command line and used to create requests and start connections to the server:

<pre>
$ ./app-client.py
usage: ./app-client.py <host> <port> <action> <value>
</pre>

Here's an example:

<pre>
$ ./app-client.py 127.0.0.1 65432 search needle
</pre>

After creating a dictionary representing the request from the command-line arguments, the host, port, and request dictionary are passed to <code>start_connection()</code>:

<pre>
def start_connection(host, port, request):
    addr = (host, port)
    print('starting connection to', addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = libclient.Message(sel, sock, addr, request)
    sel.register(sock, events, data=message)
</pre>

A socket is created for the server connection as well as a <code>Message</code> object using the request dictionary.

Like the server, the <code>Message</code> object is associated with the socket in the call to <code>sel.register()</code>. However, for the client, the socket is initially set to be monitored for both read and write events. Once the request has been written, we'll modify it to listen for read events only.

This approach gives us the same advantage as the server: not wasting CPU cycles. After the request has been sent, we're no longer interested in write events, so there's no reason to wake up and process them.

### Client Message Class

In the section [Manage Entry Point](https://realpython.com/python-sockets/#message-entry-point), we looked at how the message object was called into action when socket events were ready via <code>process_events()</code>. Now let's look at what happens after data is read and written on the socket and a message is ready to be processed by the client.

The client's message class is in <code>libclient.py</code>.

The methods appear in the class in the order in which processing takes place for a message.

The first task for the client is to queue the request:

<pre>
def queue_request(self):
    content = self.request['content']
    content_type = self.request['type']
    content_encoding = self.request['encoding']
    if content_type == 'text/json':
        req = {
            'content_bytes': self._json_encode(content, content_encoding),
            'content_type': content_type,
            'content_encoding': content_encoding
        }
    else:
        req = {
            'content_bytes': content,
            'content_type': content_type,
            'content_encoding': content_encoding
        }
    message = self._create_message(**req)
    self._send_buffer += message
    self._request_queued = True
</pre>

The dictionaries used to create the request, depending on what was passed on the command line, are in the client's main script, <code>app-client.py</code>. The request dictionary is passed as an argument to the class when a <code>Message</code> object is created.

The request message is created and appended to the send buffer, which is then seen by and sent via <code>_write()</code>. The state variable <code>self._request_queued</code> is set so <code>queue_requet()</code> isn't called again.

After the request has been sent, the client waits for a response from the server.

The methods for reading and processing a message in the client are the same as the server. As response data is read from the socket, the <code>proess</code> header methods are called: <code>process_protoheader()</code> and <code>process_jsonheader()</code>.

The difference is in the naming of the final <code>process</code> methods and the fact that they're processing a response, not creating one: <code>process_response()</code>, <code>_process_response_json_content()</code>, and <code>_process_response_binary_content()</code>. 

Last, but certainly not least, is the final call for <code>proces_response()</code>:

<pre>
def process_response(self):
    # ...
    # close when response has been processed.
    self.close()
</pre>

### Message Class Wrapup

I'll conclude the <code>Message</code> class discussion by mentioning a couple things that are important to notice with a few of the supporting methods.

Any exceptions raised by the class are caught by the main script in its <code>except</code> clause:

<pre>
try:
    message.process_events(mask)
except Exception:
    print('main: error: exception for',
        f'{message.addr}:\n{traceback.format_exc()}')
    message.close()
</pre>

Note that the last line:<code>message.close()</code>.

This is a really important line, for more than one reason! Not only does it make sure that the socket is closed, but <code>message.close()</code> also removes the socket from being monitored by <code>select()</code>. This greatly simplifies this code in the class and reduces complexity. If there's an exception or we explicitly raise one ourselves, we know <code>close()</code> will take care of the cleanup.

The methods <code>Message._read()</code> and <code>Message._write()</code> also contain something interesting:

<pre>
def _read(self):
    try:
        # should be ready to read
        data = self.sock.recv(4096)
    except BlockingIOError:
        # resource temporarily unavailable (errno EWOULDBLOCK)
        pass
    else:
        if data:
            self._recv_buffer += data
        else:
            raise RuntimeError('Peer closed')
</pre>

Note the <code>except</code> line: <code>except BlockingIOError</code>:

<code>_write()</code> has one too. These lines are important because they catch a temporary error and skip over it using pass. The temporary error is when the socket would [block](https://realpython.com/python-sockets/#blocking-calls), for example if it's waiting on the network or the other end of the connection (its peer).

By catching and skipping over the exception with <code>pass</code>, <code>select()</code> will eventually call us again, and we'll get another chance to read or write the data.

### Running the Application Client and Server

After all this hard work, let's have some fun and run some searches.

In these examples, I'll run the server so it listens on all interfaces by passing an empty string for the <code>host</code> argument. This will allow me to run the client and connect from a virtual machine that's on another network. It emulates a big-endian PowerPC machine.

First, let's start the server:

<pre>
$ ./app-server.py '' 65432
listening on ('', 65432)
</pre>

Now let's run the client and enter a search. Let's see if we can find him:

<pre>
$ ./app-client.py 10.0.1.1 65432 search morpheus
starting connection to ('10.0.1.1', 65432)
sending b'\x00d{"byteorder": "big", "content-type": "text/json", "content-encoding": "utf-8", "content-length": 41}{"action": "search", "value": "morpheus"}' to ('10.0.1.1', 65432)
received response {'result': 'Follow the white rabbit. '} from ('10.0.1.1', 65432)
got result: Follow the white rabbit. 🐰
closing connection to ('10.0.1.1', 65432)
</pre>

My terminal (iterm2 on mac) is running a shell that's using a text-encoding of Unicode (UTF-8), so the output above prints nicely with emojis.

Let's see if we can find the puppies:

<pre>
$ ./app-client.py 10.0.1.1 65432 search 🐶
starting connection to ('10.0.1.1', 65432)
sending b'\x00d{"byteorder": "big", "content-type": "text/json", "content-encoding": "utf-8", "content-length": 37}{"action": "search", "value": "\xf0\x9f\x90\xb6"}' to ('10.0.1.1', 65432)
received response {'result': '🐾 Playing ball! 🏐'} from ('10.0.1.1', 65432)
got result: 🐾 Playing ball! 🏐
closing connection to ('10.0.1.1', 65432)
</pre>

Notice the byte string sent over the network for the request in the <code>sending</code> line. It's easier to see if you look for the bytes printed in hex that represent the puppy emoji: <code>\xf0\x0f\x90\xb6</code>. I was able to [enter the emoji](https://support.apple.com/guide/mac-help/use-emoji-and-symbols-on-mac-mchlp1560/mac) for the search since my terminal is using Unicode with the encoding UTF-8.

This demonstrates that we're sending raw bytes over the network and they need to be decoded by the receiver to be interpreted correctly. This is why we went through all the trouble to create a header that contains the content type and encoding.

Here's the server output from both client connections above:

<pre>
accepted connection from ('10.0.2.2', 55340)
received request {'action': 'search', 'value': 'morpheus'} from ('10.0.2.2', 55340)
sending b'\x00g{"byteorder": "little", "content-type": "text/json", "content-encoding": "utf-8", "content-length": 43}{"result": "Follow the white rabbit. \xf0\x9f\x90\xb0"}' to ('10.0.2.2', 55340)
closing connection to ('10.0.2.2', 55340)

accepted connection from ('10.0.2.2', 55338)
received request {'action': 'search', 'value': '🐶'} from ('10.0.2.2', 55338)
sending b'\x00g{"byteorder": "little", "content-type": "text/json", "content-encoding": "utf-8", "content-length": 37}{"result": "\xf0\x9f\x90\xbe Playing ball! \xf0\x9f\x8f\x90"}' to ('10.0.2.2', 55338)
closing connection to ('10.0.2.2', 55338)
</pre>

Look at the <code>sending</code> line to see the bytes that were written to the client's socket. This is the server's response message.

You can also test sending binary requests to the server if the action argument is anything other than search:

<pre>
$ ./app-client.py 10.0.1.1 65432 binary 😃
starting connection to ('10.0.1.1', 65432)
sending b'\x00|{"byteorder": "big", "content-type": "binary/custom-client-binary-type", "content-encoding": "binary", "content-length": 10}binary\xf0\x9f\x98\x83' to ('10.0.1.1', 65432)
received binary/custom-server-binary-type response from ('10.0.1.1', 65432)
got response: b'First 10 bytes of request: binary\xf0\x9f\x98\x83'
closing connection to ('10.0.1.1', 65432)
</pre>

Since the request's <code>content-type</code> is not <code>text/json</code>, the server treats it as a custom binary type and doesn't perform JSON decoding. It simply prints the <code>content-type</code> and returns the first 10 bytes to the client:

<pre>
$ ./app-server.py '' 65432
listening on ('', 65432)
accepted connection from ('10.0.2.2', 55320)
received binary/custom-client-binary-type request from ('10.0.2.2', 55320)
sending b'\x00\x7f{"byteorder": "little", "content-type": "binary/custom-server-binary-type", "content-encoding": "binary", "content-length": 37}First 10 bytes of request: binary\xf0\x9f\x98\x83' to ('10.0.2.2', 55320)
closing connection to ('10.0.2.2', 55320)
</pre>

## Troubleshooting

### ping

<code>ping</code> will check if a host is alive and connected to the network by sending an [ICMP](https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol) echo request. It communicates directly with the operating system's TCP/IP protocol stack, so it works independently from any application running on the host.

Below is an example of running ping on macOS:

<pre>
$ ping -c 3 127.0.0.1
PING 127.0.0.1 (127.0.0.1): 56 data bytes
64 bytes from 127.0.0.1: icmp_seq=0 ttl=64 time=0.058 ms
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.165 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.164 ms

--- 127.0.0.1 ping statistics ---
3 packets transmitted, 3 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 0.058/0.129/0.165/0.050 ms
</pre>

Note the statistics at the end of the output. This can be helpful when you're trying to discover intermittent connectivity problems. For example, is there any packet loss? How much latency is there (see the round-trip times)?

If there's a firewall between you and the other host, a ping's echo request may not be allowed. Some firewall administrators implement policies that enforce this. The idea being that they don't want their hosts to be discoverable. If this is the case and you have firewall rules added to allow the hosts to communicate, make sure that the rules also allow ICMP to pass between them.

ICMP is the protocol used by <code>ping</code>, but it's also the protocol TCP and other lower-level protocols use to communicate error messages. If you're experiencing strange behavior or slow connections, this could be the reason.

ICMP messages are identified by type and code. To give you an idea of the important information they carry, here are a few:

|ICMP Type|ICMP Code|Description|
|---------|---------|-----------|
|8|0|Echo request|
|0|0|Echo reply|
|3|0|Destination network unreachable|
|3|1|Destination host unreachable|
|3|2|Destination protocol unreachable|
|3|3|Destination port unreachable|
|3|4|Fragmentation required, and DF flag set|
|11|0|TTL expired in transit|

See the article [Path MTU Discovery](https://en.wikipedia.org/wiki/Path_MTU_Discovery#Problems_with_PMTUD) for information regarding fragmentation and ICMP messages. This is an example of something that can cause strange behavior that I mentioned previously.

### netstat

In the section [Viewing Socket State](https://realpython.com/python-sockets/#viewing-socket-state), we looked at how <code>netstat</code> can be used to display information about sockets and their current state. This utility is available on macOS, Linux, and Windows.

I didn't mention the columns <code>Recv-Q</code> and <code>Send-Q</code> in the example output. These columns will show you the number of bytes that are held in network buffers that are queued for transmission or receipt, but for some reason haven't been read or written by the remote or local application.

To demonstrate this and see how much data I could send before seeing an error, I wrote a test client that connects to a test server and repeatedly calls <code>socket.send()</code>. The test server never calls <code>socket.recv()</code>. It just accpets the connection. This causes the network buffers on the server to fill, which eventually raises an error on the client.

First, I started the server:

<pre>
$ ./app-server-test.py 127.0.0.1 65432
listening on ('127.0.0.1', 65432)
</pre>
