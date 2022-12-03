from enum import Enum

# Created as part of CS391 Project 3
# Professor: Dr. George Thomas
# date: 11/29/2022
class Codes( Enum ):
    """ Represents the various codes used in the P2P messages """
    ERROR = 0       
    PEER = 1        # peer request
    FIND = 2        # find file request
    FOUND = 3       # found file
    GET = 4         # get (download) file request
    READY = 5       # ready to download file
    SEND = 6        # sending file
    QUIT = 7