# This is a sample Python script.
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files,
# tool windows, actions, and settings.
from socket import *
from threading import *
from os import listdir
from os.path import isfile, join

# this should be changed to be input variables instead
peer_name = input( "Peer name: " )  # externally provided
peer_ip = input( "Peer ip: " )  # externally provided
peer_port = input( "Peer port" )  # externally provided


################################################################################
###                  		file table class
################################################################################
class file_table( dict ):
    # creates a new dict
    def __init__( self ):
        super().__init__()
        self = dict()

    # Adds a new entry to the file table (dictionary)
    def add( self, file, file_origin_peer ):
        #peer_name, peer_ip, peer_port = file_origin_peer
        self[ file ] = file_origin_peer
        #self[ file ] = (peer_name, peer_ip, peer_port)

################################################################################
###                  		peer class
################################################################################
class peer:
    def __init__( self, peer_name, peer_ip, peer_port, directory,
                  recv_peer_ip, recv_peer_port ):
        self.peer_name = peer_name
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.directory = directory
        self.files = file_table()
        self.read_directory()
        self.lookup_port = peer_port

        name = peer_name  # this peer's name
        port = 12000
        # signals to socket that we are going to be using UDP
        udp_socket = socket( AF_INET, SOCK_DGRAM )
        udp_socket.connect( (name, port) )

        tcp_socket = socket( AF_INET, SOCK_STREAM )
        tcp_socket.connect( (name, port) )

        if recv_peer_ip is None or recv_peer_port is None:
            recv_peer_ip = -1
            recv_peer_port = -1
            self.file_transfer_port = 12000
        else:
            self.file_transfer_port = self.lookup_port + 1

    def send_file( peer_name, peer_ip, peer_port, directory, recv_peer_ip,
                   recv_peer_port ):
        if recv_peer_ip is None:
            recv_peer_ip = -1
        if recv_peer_port is None:
            recv_peer_port = -1
        one = 1

    # lookup_port is UDP,  file_transfer_port is TCP
    # code needs  lookup_port = lookup_port + 1
    def receive( lookup_port, file_transfer_port ):
        two = 1

    def read_directory( self ):
        dir_files = [ f for f in listdir( self.directory ) if isfile(join(
                self.directory, f))]
        for file in dir_files:
            self.files.add( file,
                            (self.peer_name, self.peer_ip, self.peer_port) )

    def get_files( self ):
        return self.files

    def add_file( self, file, file_origin_peer  ):
        self.files.add( self, file, file_origin_peer )