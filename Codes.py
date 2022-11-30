from enum import Enum

################################################################################
###           Represent the basic codes used for the exchange of messages
################################################################################
# FIXME: i'm not sure, but I think there might need to be more than just these
# for example, maybe have a ACK_PEER_#  or something
class Codes( Enum ):
    ERROR = 0
    PEER = 1
    FIND = 2
    HERE = 3
    GET = 4
    QUIT = 5