import threading
import traceback
import sys, time
from socket import *
from os import listdir
from os.path import isfile, join
from datetime import datetime


################################################################################
################################################################################
# TODO: ========================================================================
#  - need to update the README.txt file once we are done

## things I wrote down because I thought they might be important to me later
##       * we need to store the IP and source port to identify UDP connection
##       * we need the srcport, destport, srcip, destip

################################################################################
###                  		file table class
################################################################################
# this is intended to store a table containing the file and the originator of
# the file
class file_table( dict ):
    # creates a new dict
    def __init__( self ):
        super().__init__()
        self = dict()

    # Adds a new entry to the file table (dictionary)
    def add( self, file ):
        # peer_name, peer_ip, peer_port = file_origin_peer
        self[ file ] = file
        # self[ file ] = (peer_name, peer_ip, peer_port)


class neighbors_table( dict ):
    # creates a new dict
    def __init__( self ):
        super().__init__()
        self = dict()

    # Adds a new entry to the neighbor table (dictionary)
    def add( self, neighbor_name, neighbor_ip_port ):
        self[ neighbor ] = neighbor_ip, neighbor_port


################################################################################
###                  		peer class
################################################################################
class peer:
    def command_menu( self ):
        while self.active:
            command = input( "Your options:\n"
                             "1. [s]tatus\n"
                             "2. [f]ind <filename>\n"
                             "3. [g]et <filename> <peer IP> <peer port>\n"
                             "4. [q]uit\n"
                             "Your choice: " )
            command = str( command )
            if len( command ) <= 0:
                continue

            if command[ 0 ] == 's':
                status()
            elif command[ 0 ] == 'f':
                find()
            elif command[ 0 ] == 'g':
                one = 1
                # get()
            elif command[ 0 ] == 'q':
                print( "Peer terminated" )
                self.active = False
                time.sleep( 1 )  # delay to allow allow loops to finish and exit
                # safely if possible
                quit()
                break
            else:
                print( "Unknown command" )

    ### this essentially sets up the server-like functions of the peer
    ### it will be continuously listening for clients (other peers)
    def setup_listener_sockets( self ):
        # --------- creates the udp lookup (listener) socket -----------------#
        self.udp_lookup_socket = socket( AF_INET, SOCK_DGRAM )
        # there is no connecting (handshaking) with UDP
        # the binding only needs to occur on the server, not the client
        self.udp_lookup_socket.bind( (self.peer_ip, self.peer_port) )
        udp_listener_thread = threading.Thread(
            target = self.udp_lookup_listener, daemon = True )
        # udp_listener_thread.daemon = True
        # udp_listener_thread.setDaemon( True )                     FIXME:
        udp_listener_thread.start()
        # ---------------------------------------------------------------------#

        # --------- creates the tcp file transfer socket ----------------------#
        self.tcp_file_transfer_socket = socket( AF_INET, SOCK_STREAM )
        # TCP handshaking
        # the binding only needs to occur on the server, not the client
        self.tcp_file_transfer_socket.bind( (self.peer_ip, self.peer_port) )
        self.tcp_file_transfer_socket.listen( 256 )  # connections queue size
        tcp_listener_thread = threading.Thread(
            target = self.tcp_file_listener, daemon = True )
        # tcp_listener_thread.daemon = True
        # tcp_listener_thread.setDaemon( True )                     FIXME:

        tcp_listener_thread.start()
        # ---------------------------------------------------------------------#

    def __init__( self, peer_name, peer_ip, peer_port, directory,
                  neighbor_ip = None, neighbor_port = None ):
        self.peer_name = peer_name
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.directory = directory

        self.files = file_table()
        self.neighbors = neighbors_table()
        self.read_directory()

        self.active = True
        self.udp_lookup_socket = None
        self.tcp_file_transfer_socket = None

        self.lookup_port = peer_port  # this is our UDP port
        self.file_transfer_port = self.lookup_port + 1  # TCP port

        self.setup_listener_sockets()  # sets up the tcp/udp listener sockets

        if neighbor_ip is not None and neighbor_port is not None:
            self.add_neighbor( neighbor_ip, neighbor_port )

        self.command_menu()

    ############################################################################
    ###                  	establish neighbor connection
    ############################################################################
    def add_neighbor( self, neighbor_ip, neighbor_port ):
        udp_ephemeral = socket( AF_INET, SOCK_DGRAM )
        # I think this line only gets used in UDP               FIXME:*******
        udp_ephemeral.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )
        # tcp.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )  ******* REMOVE
        # udp_ephemeral.listen( 256 )  # connections queue size

        try:
            new_neighbor_request = self.create_response( 1, self.peer_name,
                                                         self.peer_ip,
                                                         self.peer_port )
            udp_ephemeral.sentto( new_neighbor_request,
                                  (neighbor_ip, neighbor_port) )

            # will receive a name of 256 characters
            neighbor_response, addr = udp_ephemeral.recvfrom( 256 )

            # add the neighbor response to the neighbors dictionary
            self.neighbors.add( neighbor_response.decode(),
                                (neighbor_ip, neighbor_port) )
        except Exception as error:
            print( "\tA unknown critical error occurred" )
            print( "\t" + str( error ) + "\n"
                   + traceback.format_exc() + "\n" )
        finally:
            udp_ephemeral.close()

    ############################################################################
    ###                 listens for incoming lookup requests
    ############################################################################
    def udp_lookup_listener( self ):
        print( "\t[UDP THREAD ACTIVE]\n" )

        while self.active:
            try:
                pass  # placeholder
                # do NOT have to accept since we are using UDP... I believe
                thread = threading.Thread( target = self.udp_lookup_handler,
                                           args = \
                                               self.udp_lookup_socket \
                                           .recvfrom( 256 ) )
                thread.start()  # starts the thread, start() calls run()

                print( "\t[Client accepted @ " + str(
                    datetime.now().time() ) + "  -  Total Clients: " + str(
                    num_clients ) + "]" )
            except Exception as error:
                print( "\tA unknown critical error occurred" )
                print( "\t" + str( error ) + "\n"
                       + traceback.format_exc() + "\n" )
                raise Exception()

    def udp_lookup_handler( self, byte_str, sender_ip ):
        # UDP needs to have enough space in the buffer to receive, otherwise
        # the packet will be dropped
        try:
            # (byte_str, sender_ip) = self.udp_lookup_socket.recvfrom( 4096
            # ).decode()
            # data is the byte string
            if True:
                print( "Test successfull" )
                return "Test successfull"

            action_code, name, ip, port = self.read_lookup_response( byte_str )

            if action_code != -1:
                return "Test successful"

            ### implement response logic here... ###

            # then use socket.sentto( msg, sender_up ) to respond

            # don't need to close with UDP?
        except Exception as error:
            print( "\n\tA unknown critical error occurred" )
            print(
                "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
        finally:
            self.udp_lookup_socket.close()

    ############################################################################
    ###              listens for incoming file transfer requests
    ############################################################################
    def tcp_file_listener( self ):
        print( "\t[TCP THREAD ACTIVE]\n" )

        while self.active:
            try:
                pass
                # have to accept() since we are using TCP
                thread = threading.Thread( target = self.tcp_file_handler,
                                           args =
                                           self.tcp_file_transfer_socket.accept() )
                thread.start()  # starts the thread, start() calls run()

                print( "\t[Client accepted @ " + str(
                    datetime.now().time() ) + "  -  Total Clients: " + str(
                    num_clients ) + "]" )
            except Exception as error:
                print( "\tA unknown critical error occurred" )
                print( "\t" + str( error ) + "\n"
                       + traceback.format_exc() + "\n" )

    def tcp_file_handler( self, tcp_socket, incoming_ip ):
        try:
            byte_string = tcp_socket.recv( 4096 ).decode()

        except Exception as error:
            print( "\tA unknown critical error occurred" )
            print(
                "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
        finally:
            tcp_socket.close()

    def status( self ):
        return self.neighbors, self.files

    def send_file( self, peer_name, peer_ip, peer_port, directory, recv_peer_ip,
                   recv_peer_port ):
        if recv_peer_ip is None:
            recv_peer_ip = -1
        if recv_peer_port is None:
            recv_peer_port = -1
        one = 1

    def read_directory( self ):
        # dir_files = [ f for f in listdir( self.directory ) if isfile( join(
        #     self.directory, f ) ) ]
        dir_files = { "test1.txt", "test2.txt" }

        for file in dir_files:
            self.files.add( file )

    def get_files( self ):
        return self.files

    def add_file( self, file, file_origin_peer ):
        self.files.add( self, file, file_origin_peer )

    def create_response( self, code, name, ip, port ):
        return "code={0} name={1} ip={2} port={3}\0".format(
            code, name, ip, port ).encode()

    def read_lookup_response( self, response_message ):
        msg = response_message.decode()
        field_names = { "code=", "name=", "ip=", "port=" }
        field_values = { }
        i = 0

        # if this is true, then the data has to be incorrect
        if len( msg ) <= 21:
            raise Error( "Received message is incomplete or corrupted" )

        while i < field_names.__sizeof__() - 1 \
                and msg.index( fields[ i ] ) > -1:
            start = len( msg.index( field_names[ i ] ) + field_names[ i ] )
            end = len( msg.index( field_names[ i + 1 ] ) + field_names[ i + 1
                                                                        ] )

            if start >= len( msg ) or end < 0:
                raise Error( "Received message is incomplete or corrupted" )

            field_values[ i ] = msg[ start: end ]

            i += 1
        action_code = int( field_values[ 0 ] )
        name = str( field_values[ 1 ] )
        ip = str( field_values[ 2 ] )
        port = int( field_values[ 3 ] )

        return action_code, name, ip, port

    def quit( self ):
        # needs to send messages to neighbors and attempt to close threads
        # safely
        self.udp_lookup_socket.close()
        self.tcp_file_transfer_socket.close()


################################################################################
################################ main ##########################################
################################################################################
# my_peer = peer( "A", "localhost", 2222, "p3/files" )
my_peer = peer( sys.argv[ 1 ], sys.argv[ 2 ], int( sys.argv[ 3 ] ),
                sys.argv[ 4 ] )
################################################################################
############################## end main ########################################
###############################################################################