import threading
import traceback
import sys, time, os
import Message_Table, Neighbor_Table, File_Table
import Codes
from socket import *
from Message_Table import Message_Table
from Neighbor_Table import Neighbor_Table
from File_Table import File_Table
from Message import Message
from Codes import Codes
from os.path import isfile, join
from datetime import datetime
from enum import Enum

# Created as part of CS391 Project 3
# Professor: Dr. George Thomas
# date: 11/29/2022
class Tcp_Message( Message ):
    """ Represents a TCP message (part pf a segment) """
    def __init_subclass__( cls, **kwargs ):
        """ Constructor for the UDP message object
        :param kwargs: takes in a variable number of arguments regarding the
        details of this message object
        """
        super().__init__( kwargs = kwargs )
            
    def send_file( self, tcp_socket, dir_path ):
        """ Sends a file over a TCP connection
        :param dir_path: the path to the file
        :param tcp_socket: the socket that the file is being sent on
        :return: n/a
        """
        if self.file is None:
            return
        file = open( os.path.join( dir_path, self.file ), "rb" )  
                                                        # rb = read  binary
        binary_file_data = file.read( 1024 )  # send 1 byte

        while binary_file_data:
            tcp_socket.send( binary_file_data )
            binary_file_data = file.read( 1024 )
        file.close()
        tcp_socket.shutdown( SHUT_WR )      # stops reading and writing