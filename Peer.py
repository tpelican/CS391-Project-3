# This is a sample Python script.
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files,
# tool windows, actions, and settings.
from socket import *

name = "peername"     # this peer's name
port = 12000;
socket = socket( AF_INET, SOCK_DGRAM )
socket.connect((name, port))

def send_file( peer_name, peer_ip, peer_port, directory, recv_peer_ip,
               recv_peer_port ):
    if recv_peer_ip is None:
        recv_peer_ip = -1
    if recv_peer_port is None:
        recv_peer_port = -1
    one = 1

def receive( peer_name, peer_ip, peer_port, directory, recv_peer_ip,
               recv_peer_port ):
    two = 1

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
