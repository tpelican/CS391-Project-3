import sys, time, os
from socket import *
from Message import Message

# Created as part of CS391 Project 3
# Professor: Dr. George Thomas
# date: 11/29/2022
class Udp_Message( Message ):
    """ Represents a UDP message """
    def __init_subclass__( cls, **kwargs ):
        """ Constructor for the UDP message object
        :param kwargs: takes in a variable number of arguments regarding the
        details of this message object
        """
        super().__init__( kwargs = kwargs )

    def send( self, accept_reply = False ):
        """ Sends a UDP message out on an ephemeral port
        :param accept_reply: whether to accept an immediate reply
        :return: the replied UDP if accept_reply is true, else n/a
        """
        try:
            udp_ephemeral = socket( AF_INET, SOCK_DGRAM )
            udp_ephemeral.sendto( self.codify(),
                                  (self.get_dest_ip(), self.get_dest_port()) )
            if accept_reply is True:
                response, addr = udp_ephemeral.recvfrom( 2048 )
                return Udp_Message( response_msg = response.decode() )

            udp_ephemeral.close()
        except Exception as error:
            print( "\tAn unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )