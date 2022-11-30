import threading
import traceback
import sys, time, os
import Message_Table, Neighbor_Table, File_Table
import Udp_Message, Codes
from socket import *
from Message_Table import Message_Table
from Neighbor_Table import Neighbor_Table
from File_Table import File_Table
from Udp_Message import Udp_Message
from Codes import Codes
from os.path import isfile, join
from datetime import datetime
from enum import Enum

################################################################################
###          Class for representing and working with UDP messages
################################################################################
class Udp_Message:

    def __init__( self, **kwargs ):
        keys = { 'self', 'code', 'src_name', 'src_ip',
                         'src_port', 'dest_name', 'dest_ip', 'dest_port',
                         'file', 'seq', 'ftp', 'response_msg' }
        self.message = ""
        self.__dict__.update( (k, v) for k, v in kwargs.items() if k in keys )

        if self.__dict__.__contains__('response_msg'):
            self.decodify()

    def action_code( self ):
        match self.code:
            case 'Codes.PEER':
                return Codes.PEER
            case 'Codes.FIND':
                return Codes.FIND
            case 'Codes.HERE':
                return Codes.HERE
            case 'Codes.GET':
                return Codes.GET
            case 'Codes.QUIT':
                return Codes.QUIT
            case _:
                return Codes.ERROR

    def get_name( self ):
        return self.src_name

    def get_src_ip( self ):
        return self.src_ip

    def get_src_port( self ):
        if self.__dict__.__contains__( 'src_port' ):
            return int( self.src_port )

    def get_dest_ip( self ):
        return self.dest_ip

    def get_dest_port( self ):
        if self.__dict__.__contains__( 'dest_port' ):
            return int( self.dest_port )

    def get_filename( self ):
        return self.file

    def get_seq_num( self ):
        return self.seq

    def get_ftp( self ):
        if self.__dict__.__contains__( 'ftp' ):
            return int( self.ftp )

    def get_msg_content( self ):
        return self.message

    def send( self, accept_reply = False ):
        try:
            udp_ephemeral = socket( AF_INET, SOCK_DGRAM )
            udp_ephemeral.sendto( self.codify(),
                                  (self.dest_ip, self.get_dest_port()) )

            if accept_reply is True:
                response, addr = udp_ephemeral.recvfrom( 2048 )
                return Udp_Message( response_msg = response.decode() )

            udp_ephemeral.close()
        except Exception as error:
            print( "\tA unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )

    def codify( self ):
        response_str = ""
        for (attribute, value) in self.__dict__.items():
            if attribute == 'code' or attribute == 'ftp' or \
                attribute == 'src_port' or attribute == 'dest_port':

                response_str += attribute + "={" + str( value ) + "}"
            else:
                response_str += attribute + "={" + value + "}"

        response_str += "\0"
        self.message = response_str
        return response_str.encode()

    def decodify( self ):
        response = self.response_msg
        keys = [ "self", "code", "src_name", "src_ip",
                         "src_port", "dest_name", "dest_ip", "dest_port",
                         "file", "seq", "ftp" ]
        i = 0
        start = 0
        index = -1
        while i < len( keys ):
            if keys[ i ] in response:
                index = response.index( keys[ i ] + "={", start )

            if index > -1:
                start = index + len( keys[ i ] + "={" )
                end = response.index( "}", start )
                value = response[ start:end ].strip()

                if value == 'code' or value == 'ftp' or \
                        value == 'src_port' or value == 'dest_port':
                    setattr( self, keys[ i ], int( value ) )
                else:
                    setattr( self, keys[ i ], value )

                start = end + 1

            index = -1
            i += 1

        return self

    # I tried making a method like this, but it didn't quite pan out the way
    # I wanted it to. I'm leaving it here for now in case I decide to come
    # back to it                        FIXME:
    def reply( self, sender_address ):
        print( "made it to the reply " )
        udp_ephemeral = socket( AF_INET, SOCK_DGRAM )
        # udp_ephemeral.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )
        udp_ephemeral.sendto( self.codify(), sender_address )
        udp_ephemeral.close()