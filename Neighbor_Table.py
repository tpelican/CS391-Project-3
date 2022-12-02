################################################################################
###                  	  Neighbors table class
################################################################################
class Neighbor_Table( dict ):
    def __init__( self ):
        """ Creates a new Neighbor_Table dictionary
        """
        super().__init__()
        self = dict()

    def add( self, peer_name, peer_ip, peer_port, send_base ):
        """ Adds a new Neighbor key-value pair
        :param peer_name: the name of the neighboring peer
        :param peer_ip: the ip of the neighboring peer
        :param peer_port: the lookup port of the neighboring peer
        :param send_base: the starting base of non-ACK'd messages
        :return: n/a
        """
        self[ peer_name ] = peer_ip, peer_port, send_base

    def increment_seq( self, peer_name ):
        (peer_ip, peer_port, send_base) = self[ peer_name ]
        send_base += 1
        self[ peer_name ] = (peer_ip, peer_port, send_base)