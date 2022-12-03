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
    """ Represents a TCP message """
    def __init_subclass__( cls, **kwargs ):
        """ Constructor for the UDP message object
        :param kwargs: takes in a variable number of arguments regarding the
        details of this message object
        """
        super().__init__( kwargs = kwargs )

    def send( self, tcp_socket ):
        """ In progress, not sure if this will get used   FIXME:
        :param tcp_socket: 
        :return: 
        """
        try:
            pass
            b = self.codify()

        except Exception as error:
            print( "\tAn unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
            
    def send_file( self, tcp_socket ):
        """ Sends a file over a TCP connection
        :param tcp_socket: 
        :return: 
        """
        if self.file is None:
            return

        # print(" Send " + filename + " to:  ip=" + self.get_dest_ip() + 
        #       "  ftp=" + str(self.get_ftp()))

        file = open( self.file, "rb" )  # rb = read binary
        binary_file_data = file.read( 1024 )  # send 1 byte

        while binary_file_data:
            print( "sending..." )               # FIXME:
            tcp_socket.send( binary_file_data )
            binary_file_data = file.read( 1024 )
            
        file.close()
        print("Completed send")
        
        tcp_socket.shutdown( SHUT_WR )      # stops reading and writing