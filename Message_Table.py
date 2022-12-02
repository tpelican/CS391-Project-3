################################################################################
###                  	  Lookup_Requests Table
################################################################################
class Message_Table( dict ):
    def __init__( self ):
        """ Creates a new Neighbor_Table dictionary
        """
        super().__init__()
        self = dict()

    def add( self, peer_name, peer_seq ):
        """ Adds a new Neighbor key-value pair
        :param peer_name: the name of the neighboring peer
        :param peer_seq: the sequence number of the request
        :return: n/a
        """
        self[ peer_name, peer_seq ] = peer_name, peer_seq
