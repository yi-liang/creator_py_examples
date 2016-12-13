"""
This is a python example (using awa client api) of workshop1 switch counter
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

from letmecreate.core import switch
from letmecreate.core.switch import SWITCH_1_PRESSED, SWITCH_2_PRESSED

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
url = "udp://" + "127.0.0.1" + ":" + str(6004)
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
                <ObjectID>3200</ObjectID>
                <Properties>
                    <Property>
                        <PropertyID>5501</PropertyID>
                        <DataType>Integer</DataType>
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
request.add((3200, 0))
response = ipc.send_request_and_receive_response(url, request.serialize())
print(response)

# Create resource
request = client.CreateRequest(session_id=mysession_id)
request.add((3200, 0, 5501))
response = ipc.send_request_and_receive_response(url, request.serialize())
print(response)


counter = 0


def switch_pressed():
    global counter
    counter += 1
    print("pressed", counter)
    # Set resource value
    request = client.SetRequest(session_id=mysession_id)
    request.add((3200, 0, 5501), counter)
    response = ipc.send_request_and_receive_response(url, request.serialize())
    print(response)

switch.init()
switch.add_callback(SWITCH_1_PRESSED | SWITCH_2_PRESSED, switch_pressed)


while True:
    pass


