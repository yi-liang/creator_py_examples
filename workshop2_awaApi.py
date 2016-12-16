"""
This is a python example (using awa client api) of workshop2 - RemoteRelay
To run it: (1) Install the following packages on ci40:
opkg install python3-letmecreate python3-ctypes awalwm2m
(2) Make sure awa python api is available in the python package on ci40
 e.g. scp <python api directory> root@<ci40 IP>:/usr/lib/python3.5/site-packages/awa
(3) Get the "PSK"(identity and secret) from "Device Keys" on the dev console
(4) copy this python file to the ci40, then run "python3 <identity> <secret>".
"""
from awa import ipc_lwm2m_client as client
from awa import ipc_lwm2m_server as server
from awa import ipc
import socket
from letmecreate.core import led

import subprocess
from shlex import split
from sys import argv
from time import sleep

PORT = 6003
IPC_PORT = 6004
CLIENT_NAME = "test"

if len(argv) < 3:
    raise Exception("missing identity/secret, run 'python3 <identity> <secret>'")
identity = argv[1]
secret = argv[2]


# Start daemon
cmd = "awa_clientd --port "+str(PORT)+" --ipcPort "+str(IPC_PORT)+" --endPointName "+CLIENT_NAME+" --bootstrap coaps://deviceserver.creatordev.io:15684 --pskIdentity="+identity+" --pskKey="+secret
subprocess.Popen(split(cmd))
sleep(10)


# Connect
url = "udp://" + "127.0.0.1" + ":" + str(IPC_PORT)
request = server.ConnectRequest(session_id=None)
response = ipc.send_request_and_receive_response(url, request.serialize())

# Get the session ID
mysession_id = server.ConnectResponse(response).session_id
print("Session ID %s" % (mysession_id,))

# Create Object
request = client.DefineRequest(session_id=mysession_id)
request.define_data("""<Content>
        <ObjectDefinitions>
            <ObjectMetadata>
                <ObjectID>3201</ObjectID>
                <Properties>
                    <Property>
                        <PropertyID>5550</PropertyID>
                        <DataType>Boolean</DataType>
                    </Property>
                </Properties>
            </ObjectMetadata>
        </ObjectDefinitions>
    </Content>
""")
response = ipc.send_request_and_receive_response(url, request.serialize())
print(response)

# Create Object instance
request = client.CreateRequest(session_id=mysession_id)
request.add((3201, 0))
response = ipc.send_request_and_receive_response(url, request.serialize())
print(response)

# Create resource
request = client.CreateRequest(session_id=mysession_id)
request.add((3201, 0, 5550))
response = ipc.send_request_and_receive_response(url, request.serialize())
print(response)

# Subscribe to resource value change
request = client.SubscribeToChangeRequest(session_id=mysession_id)
request.add((3201, 0, 5550))
response = ipc.send_request_and_receive_response(url, request.serialize())
print(response)

# Establish Notify
request = client.EstablishNotify(session_id=mysession_id)
response = ipc.send_request_and_receive_response(url, request.serialize())
print(response)

# Socket receiving notification
sentxml = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiving = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
receiving.bind(('127.0.0.1', int(IPC_PORT)))

led.init()


def handler_func():
    request = client.GetRequest(session_id=mysession_id)
    request.add((3201, 0, 5550))
    response = ipc.send_request_and_receive_response(url, request.serialize())
    result = client.GetResponse(response).getValue((3201, 0, 5550))
    print(result)
    if result == "True":
        led.switch_on(led.ALL_LEDS)
    else:
        led.switch_off(led.ALL_LEDS)


while True:
    data, address = receiving.recvfrom(65536)
    if "<Notification>" in str(data):
        handler_func()
        print("Received Notification")
        print(data)
