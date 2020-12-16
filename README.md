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

Notice that <code>Local Address</code> is ::1.65432. If echo-server.py had used <code>HOST = ''</code> instead of <code>HOST = '127.0.0.1'</code>, netstat would show this:

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
We want a client and server that handles errors appropriately so other connections aren't affected. Obviously, our client or server shouldn't come crashing down in a ball of fury if an exception isn't caught. This is something we haven't discussed up until now. I've intentionally left out eg rfor brevity and clarity in the examples.

Now that you're familiar with the basic API, non-blocking sockets, and <code>select()</code>, we can add some error handling and discuss the "elephant in the room" that I've kept hidden from you behind that large curtain over there. Yes, I'm talking about the custom class I mentioned way back in the introduction. I know you wouldn't forget.

First, let's address the errors:

`"All errors raise exceptions. The normal exceptions for invalid argument types and out-of-memory conditions can be raised; starting from Python 3.3, errors related to socket or address semantics raise OSError or one of its subclasses.`

We need to catch OSError. Another thing I haven't mentioned in relation to errors is timeouts. You'll see them discussed in many places in the documentation. Timeouts happen and are a "normal" error. Hosts and routers are rebooted, switch ports go bad, cables go bad, cables get unplugged, you name it. You should be prepared for these and other errors and handle them in your code.

What about the "elephant in the room?" As hinted by the socket type socket.SOCK_STREAM, when using TCP, you're reading from a continuous stream of bytes. It's like reading from a file on disk, but instead you're reading bytes from the network.

However, unlike reading a file, there's no f.seek(). In other words, you can't reposition the socket pointer, if there was one, and move randomly around the data reading whatever, whenever you'd like.

When bytes arrive at your socket, there are network buffers involved. Once you've read them, they need to be saved somewhere. Calling recv() again reads the next stream of bytes available from the socket.

What this means is that you'll be reading from the socket in chunks. You need to call recv() and save the data in a buffer until you've read enough bytes to have a complete message that makes sense to your application.

It's up to you to define and keep track of where the message boundaries are. As far as the TCP socket is concerned, it's just sending and receiving raw bytes to and from the network. It knows nothing about what those raw bytes mean.

This brings us to defining and application-layer protocol. What's an application-layer protocol? Put simply, your application will send and receive messages. These messages are your application's protocol.

In other words, the length and format you choose for these messages define the semantics and behavior of your application. This is directly related to what I explained in the previous paragraph regarding reading bytes from the socket. When you're reading bytes with recv(), you need to keep up with how many bytes were read and figure out where the message boundaries are.

How is this done? One way is to always send fixed-length messages. If they're always the same size, then it's easy. When you've read that number of bytes into a buffer, then you know you have one complete message.

However, using fixed-length messages is inefficient for small messages where you'd need to use padding to fill them out. Also, you're still left with the problem of what to do about data that doesn't fit into one message.

In this tutorial, we'll take a generic approach. An approach that's used by many protocols, including HTTP. We'll prefix messages with a header that includes the content length as well as any other fields we need. By doing this, we'll only need to keep up with the header. Once we've read the header, we can process it to determine the length of the message's content and then read that number of bytes to consume it.

We'll implement this by creating a custom class that can send and receive messages that contain text or binary data. You can improve and extend it for your own applications. The most important thing is that you'll be able to see an example of how this is done.

I need to mention something regarding sockets and bytes that may affect you. As we talked about earlier, when sending and receiving data via sockets, you're sending and receiving raw bytes.

If you receive data and want to use it in a context where it's interpreted as multiple bytes, for example a 4-byte integer, you'll need to take into account that it could be in a format that's not native to your machine's CPU. The client or server on the other end could have a CPU that uses a different byte order than your own. If this is the case, you'll need to convert it to your host's native byte order before using it.

This byte order is referred to as a CPU's endianness. See Byte Endianness in the reference section for details. We'll avoid this issue by taking advantage of Unicode for our message header and using the encoding UTF-8. Since UTF-8 uses an 8-bit encoding, there are no byte ordering issues.

You can find an explanation in Python's Encodings and Unicode documentation. Note that this applies to the text header only. We'll use an explicit type and encoding defined in the header for the content that's being sent, the message payload. This will allow us to transfer any data we'd like (text or binary), in any format.

You can easily determine the byte order of your machine by using sys.byteorder. For example, on my Intel laptop, this happens:

python3 -c 'import sys; print(repr(sys.byteorder))'
'little'

If I run this in a virtual machine that emulates a big-endian CPU (PowerPC), then this happens:

python3 -c 'import sys; print(repr(sys.byteorder))'
'big'

In this example application, our application-layer protocol defines the header as Unicode text with a UTF-8 encoding. For the actual content in the message, the message payload, you'll have to swap the byte order manually if needed. This will depend on your application and whether or not it needs to process multi-byte binary data from a machine with different endianness. You can help your client or server implement binary support by adding additional headers and using them to pass parameters, similar to HTTP.

Don't worry if this doesn't make sense yet. In the next section, you'll see how all of this works and fits together.

Application Protocol Header
Let's fully define the protocol header. The protocol header is:
  Variable length text
  Unicode with the encodoing UTF-8
  A Python dictionary serialized using JSON

The required headers, or sub-headers, in the protocol header's dictionary are as follows:

byteorder - the byte order of the machine (uses sys.byteorder). This may not be required for your application
content-length - the length of the content in bytes
content-type - the type of content in the payload, for example, text/json or binary/my-binary-type
content-encoding - the encoding used by the content, for example, utf-8 for Unicode text or binary for binary data.

These headers inform the receiver about the content in the payload of the message. This allows you to send arbitrary data while providing enough information so the content can be decoded and interpreted correctly by the receiver. Since the headers are in a dictionary, it's easy to add additional headers by inserting key/value pairs as needed.

Sending an Application Message
There's still a bit of a problem. We have a variable-length header, which is nice and flexible, but how do you know the length of the header when reading it with recv()?

When we previously talked about using recv() and message boundaries, I mentioned that fixed-length headers can be inefficient. That's true, but we're going to use a small, 2-byte, fixed-length header to prefix the JSON header that contains its length.

You can think of this as a hybrid approach to sending messages. In effect, we're bootstrapping the message receive process by sending the length of the header first. This makes it easy for our receiver to deconstruct the message.

To give you a better idea of the format, let's look at a message in its entirety:

MESSAGE

Fixed Length Header
Type: 2 byte integer
Byte Order: network (big-endian)

Variable-length JSON Header
Type: Unicode text
Encoding: UTF-8
Length: specified by fixed-length header

Variable-length Content
Type: specified in JSON header
Encoding: specified in JSON header
Length: specified in JSON Header


A message starts with a fixed-length header of 2-bytes that's an integer in network byte order. This is the length of the next header, the variable-length JSON header. Once we've read 2 bytes with recv(), then we know we can process the 2 bytes as an integer and then read that number of bytes before decoding the UTF-8 JSON header.

The JSON header contains a dictionary of additional headers. One of those is content-length, which is the number of bytes of the message's content (not including the JSON header). Once we've called recv() and read content-length bytes, we've reached a message boundary and read an entire message.

Application Message Class
Finally the payoff! Let's look at the Message class and see how it's used with select() when read and write events happen on the socket.

For this example application, I had to come up with an idea for what types of messages the client and server would use. We're far beyond toy echo clients and servers at this point.

To keep things simple and still demonstrate how thing would work in a real application, I created an application protocol that implements a basic search feature. The client sends a search request and the server does a lookup for a match. If the request sent by the client isn't recognized as a search, the server assumes it's a binary request and returns a binary response.

After reading the following sections, running the examples, and experimenting with the code, you'll see how things work. You can then use the Message class as a starting point and modify it for your own use.

We're really not that far off from the "multiconn" client and server example. The event loop code stays the same in app-client.py and app-server.py. What I've done is move the message code into a class named Message and added methods to support reading, writing, and processing of the headers and content. This is a great example for using a class.

As we discussed before and you'll see below, working with sockets involves keeping state. By using a class, we keep all of the state, data, and code bundled together in an organized unit. An instance of the class is created for each socket in the client and server when a connection is started or accepted.

The class is mostly the same for both the client and the server for the wrapper and utility methods. They start with an underscore, like <code>Message._json_encode()</code>. These methods simplify working with the class. They help other methods by allowing them to stay shorter and support the DRY principle.

The server's Message class works in essentially the same way as the client's and vice-versa. The difference being that the client initiates the connection and sends a request message, followed by processing the server's response message. Conversely, the server waits for a connection, processes the client's request message, and then sends a response message.

It looks like this:

|Step|Endpoint|Action/Message Content|
|----|--------|----------------------|
|1|Client|Sends a Message containing request content|
|2|Server|Receives and processes client request Message|
|3|Server|Sends a Message containing response content|
|4|Client|Receives and processes server response Message|

Here's the file and code layout:

|Application|File|Code|
|-----------|----|----|
|Server|app-server.py|The server's main script|
|Server|libserver.py|The server's Message class|
|Client|app-client.py|The client's main script|
|Client|libclient.py|The client's Message class|

Message Entry Point
I'd like to discuss how the message class works by first mentioning an aspect of its design that wasn't immediately obvious to me. Only after refactoring it at least five times did I arrive at what it is currently. Why? Managing state.

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

