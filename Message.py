import sys, os
from socket import *
from Codes import Codes
from abc import ABC

# Created as part of CS391 Project 3
# Professor: Dr. George Thomas
# date: 11/28/2022
class Message( ABC ):
    """ Represents a message over a transport protocol """

    def __init__( self, **kwargs ):
        """ Constructor for the message object
        :param kwargs: takes in a variable number of arguments regarding the
        details of this message object
        """
        self.keys = [ 'self', 'code', 'src_name', 'src_ip',
                      'src_port', 'dest_name', 'dest_ip', 'dest_port',
                      'file', 'seq', 'ftp', 'response_msg' ]
        self.__dict__.update( (k, v) for k, v in kwargs.items()
                              if k in self.keys )
        self.message = ""

        if self.__dict__.__contains__( 'response_msg' ):
            self.decodify()

    def action_code( self ):
        """ Returns the code attribute as an enum of type Codes
        :return: the action code as an enum of type Codes
        """
        match self.code:
            case 'Codes.PEER':
                return Codes.PEER
            case 'Codes.FIND':
                return Codes.FIND
            case 'Codes.FOUND':
                return Codes.FOUND
            case 'Codes.GET':
                return Codes.GET
            case 'Codes.READY':
                return Codes.READY
            case 'Codes.SEND':
                return Codes.SEND
            case 'Codes.QUIT':
                return Codes.QUIT
            case _:
                return Codes.ERROR

    def get_name( self ):
        """ Returns the name of the message sender
        :return: the name of the message sender
        """
        return self.src_name

    def get_src_ip( self ):
        """ Returns the source ip attribute
        :return: the source ip attribute
        """
        return self.src_ip

    def get_src_port( self ):
        """ Returns the source port attribute as an int
        :return: the source port attribute as an int
        """
        if self.__dict__.__contains__( 'src_port' ):
            return int( self.src_port )

    def get_dest_ip( self ):
        """ Returns the destination ip attribute
        :return: the destination ip attribute
        """
        return self.dest_ip

    def get_dest_port( self ):
        """ Returns the destination port attribute as an int
        :return: the destination port attribute as an int
        """
        if self.__dict__.__contains__( 'dest_port' ):
            return int( self.dest_port )

    def get_filename( self ):
        """ Returns the name of the file
        :return: the name of the file
        """
        return self.file

    def get_seq_num( self ):
        """ Returns the seq attribute as an int
        :return: Returns the seq attribute as an int
        """
        if self.__dict__.__contains__( 'seq' ):
            return int( self.seq )

    def get_ftp( self ):
        """ Returns the file transfer port number as an int
        :return: the file transport number attribute as int
        """
        if self.__dict__.__contains__( 'ftp' ):
            return int( self.ftp )

    def codify( self ):
        """ Converts this Messages attributes to an encoded string
        :return: an encoded string containing this message
        """
        response_str = ""
        for (attribute, value) in self.__dict__.items():
            if attribute == 'self' or attribute == 'message' or attribute \
                    == 'response_msg' or attribute == 'keys':
                continue

            if attribute == 'code' or attribute == 'ftp' or \
                    attribute == 'src_port' or attribute == 'dest_port' \
                    or attribute == 'seq':
                response_str += attribute + "={" + str( value ) + "}"
            else:
                response_str += attribute + "={" + value + "}"
        response_str += "\0"
        self.message = response_str
        
        return response_str.encode()


    def decodify( self ):
        """ Parses the received response string and updates the variables
        :return: returns this Message object
        """
        response = self.response_msg
        keys = self.keys
        i = 0
        index = -1

        while i < len( keys ):
            if keys[ i ] in response:
                index = response.index( keys[ i ] + "={", 0 )

            if index > -1:
                start = index + len( keys[ i ] + "={" )
                end = response.index( "}", start )
                value = response[ start:end ].strip()

                if value == 'code' or value == 'ftp' or \
                        value == 'src_port' or value == 'dest_port' \
                        or value == 'seq':
                    setattr( self, keys[ i ], int( value ) )
                elif value != 'self' and value != 'message' \
                        and value != 'response_msg' and value != 'keys':
                    setattr( self, keys[ i ], value )

            index = -1
            i += 1

        return self

    def to_string( self ):
        """ Converts this message to a string
        :return:
        """
        self.codify()
        return self.message