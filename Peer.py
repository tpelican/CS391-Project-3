import threading
import traceback
import sys, time, os
from socket import *
from os.path import isfile, join
from datetime import datetime


################################################################################
################################################################################
# TODO: ========================================================================
#  - need to update the README.txt file once we are done

# MESSAGE FORMAT:  code={0} name={1} ip={2} port={3}
# Action Codes:                                         (for now)
#   0 - error
#   1 - add peer
#   2 - file inquiry request
#   3 - file download request

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

################################################################################
###                  	  Neighbors table class
################################################################################
class neighbors_table( dict ):
    # creates a new dict
    def __init__( self ):
        super().__init__()
        self = dict()

    # Adds a new entry to the neighbor table (dictionary)
    def add( self, neighbor_name, neighbor_ip, neighbor_port ):
        self[ neighbor_name ] = neighbor_ip, neighbor_port


################################################################################
###                  		Peer class
################################################################################
class peer:
    def command_menu( self ):
        while self.active:
            self.print_command_menu()
            command = str( input() )
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

    def print_command_menu( self ):
        print( "Your options:\n"
                         "1. [s]tatus\n"
                         "2. [f]ind <filename>\n"
                         "3. [g]et <filename> <peer IP> <peer port>\n"
                         "4. [q]uit\n"
                         "Your choice: " )

    ### this essentially sets up the server-like functions of the peer
    ### it will be continuously listening for clients (other peers)
    def setup_listener_sockets( self ):
        # --------- creates the udp lookup (listener) socket -----------------#
        self.udp_lookup_socket = socket( AF_INET, SOCK_DGRAM )
        # there is no connecting (handshaking) with UDP
        # the binding only needs to occur on the server, not the client
        # here we set the binding because we want a static port
        self.udp_lookup_socket.bind( (self.peer_ip, self.peer_port) )
        threading.Thread( target = self.udp_lookup_listener,
                          daemon = True ).start()
        # ---------------------------------------------------------------------#

        # --------- creates the tcp file transfer socket ----------------------#
        self.tcp_file_transfer_socket = socket( AF_INET, SOCK_STREAM )
        # TCP handshaking
        # the binding only needs to occur on the server, not the client
        self.tcp_file_transfer_socket.bind( (self.peer_ip, self.peer_port) )
        self.tcp_file_transfer_socket.listen( 256 )  # connections queue size
        threading.Thread( target = self.tcp_file_listener,
                          daemon = True ).start()
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
            self.connect_to_neighbor( neighbor_ip, neighbor_port )

        self.command_menu()

    ############################################################################
    ###                  	establish neighbor connection
    ############################################################################
    def connect_to_neighbor( self, neighbor_ip, neighbor_port ):
        udp_ephemeral = socket( AF_INET, SOCK_DGRAM )

        # I don't think this method needs to be on its own thread since it
        # only executes once
        # I think this line only gets used in TCP               FIXME:*******
        # udp_ephemeral.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )

        # tcp.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )  ******* REMOVE
        # udp_ephemeral.listen( 256 )  # connections queue size
        try:
            new_neighbor_request = self.create_response( 1, self.peer_name,
                                                         self.peer_ip,
                                                         self.peer_port )
            udp_ephemeral.sendto( new_neighbor_request.encode(),
                                  (neighbor_ip, neighbor_port) )

            # will receive a name of 256 characters, we only need to receive
            # the name here since that's all that needs to be sent at this stage
            neighbor_name, addr = udp_ephemeral.recvfrom( 2048 )

            # FIXME: remove this -- for testing
            self.print_ports( neighbor_name.decode(), neighbor_port,
                              str(addr[ 1 ] ), neighbor_name.decode() )

            # add the neighbor response to the neighbors dictionary
            self.add_neighbor( neighbor_name.decode(),
                               neighbor_ip, neighbor_port )
            self.print_connection_msg( neighbor_name.decode(), neighbor_ip,
                                       neighbor_port )

        except Exception as error:
            print( "\tA unknown critical error occurred" )
            print( "\t" + str( error ) + "\n"
                   + traceback.format_exc() + "\n" )
        finally:
            udp_ephemeral.close()
            return

    # adds a neighbor to the neighbor dictionary
    def add_neighbor( self, neighbor_name, neighbor_ip, neighbor_port ):
        self.neighbors.add( neighbor_name, neighbor_ip, neighbor_port )

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

            except Exception as error:
                print( "\tA unknown critical error occurred" )
                print( "\t" + str( error ) + "\n"
                       + traceback.format_exc() + "\n" )
                raise Exception()  # FIXME:

    def udp_lookup_handler( self, sender_msg, sender_address ):
        # UDP needs to have enough space in the buffer to receive, otherwise
        # the packet will be dropped
        try:
            # (byte_str, sender_ip) = self.udp_lookup_socket.recvfrom( 4096
            # ).decode()
            # data is the byte string

            # FIXME: not actually need the sender ip in the reponse msg

            (sender_ip, socket_port) = sender_address

            action_code, sender_name, sender_ip, sender_lookup_port = \
                self.read_lookup_response( sender_msg )

            sock = socket( AF_INET, SOCK_DGRAM )
            # binds to the port that the sender sent on
            # sock.bind( ('', socket_port) )
            msg = "TEST"

            if action_code == 0:
                pass  # action_code 0 was created in case we need it for errors
            elif action_code == 1:  # ACK
                self.add_neighbor( sender_name, sender_ip, sender_lookup_port )
                msg = self.peer_name
                self.print_acceptance_msg( sender_name, sender_ip,
                                           sender_lookup_port )
            elif action_code == 2:
                pass
            elif action_code == 3:
                pass
            elif action_code == 4:
                pass
            else:
                pass
            self.print_ports( sender_name, sender_lookup_port, socket_port,
                              sender_msg.decode() )
            # currently, i think this means it gets sent on ephemeral port
            sock.sendto( msg.encode(), sender_address )
            sock.close()
            # don't need to close with UDP?
        except Exception as error:
            print( "\n\tA unknown critical error occurred" )
            print(
                "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
        finally:
            self.print_command_menu()

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
        dir_files = os.listdir( self.directory )
        print( dir_files )
        for file in dir_files:
            self.files.add( file )

    def get_files( self ):
        return self.files

    def add_file( self, file, file_origin_peer ):
        self.files.add( self, file, file_origin_peer )

    # returns an encoded response -- note the null terminating character
    def create_response( self, code, name, ip, port ):
        return "code={0} name={1} ip={2} port={3}\0".format(
            code, name, ip, port )

    def read_lookup_response( self, response_message ):
        msg = response_message.decode()
        field_names = [ "code=", "name=", "ip=", "port=" ]
        field_values = [ ]
        i = 0

        # if this is true, then the data has to be incorrect
        if len( msg ) <= 21:
            raise Error( "Received message is incomplete or corrupted" )

        while i < 4 and msg.index( field_names[ i ] ) > -1:

            # this should be more robust                        FIXME:
            start = msg.index( field_names[ i ] ) + len( field_names[ i ] )
            if i < 3:
                end = msg.index( field_names[ i + 1 ], start )
            else:
                end = len( msg ) - 1
            field_values.append( msg[ start:end ].strip() )

            # if start >= len( msg ) or end < 0:
            #     raise Error( "Received message is incomplete or corrupted" )

            i += 1
        action_code = int( field_values[ 0 ] )
        name = str( field_values[ 1 ] )
        ip = str( field_values[ 2 ] )
        port = int( field_values[ 3 ] )

        return action_code, name, ip, port

    def print_acceptance_msg( self, name, ip, port ):
        print( "\n{0}: Accepting {1} {2}:{3}".format(
            self.peer_name, name, ip, port ) )

    def print_connection_msg( self, name, ip, port ):
        print( "{0}: Connected {1} {2}:{3}\n".format(
            self.peer_name, name, ip, port ) )

    def quit( self ):
        # needs to send messages to neighbors and attempt to close threads
        # safely
        self.udp_lookup_socket.close()
        self.tcp_file_transfer_socket.close()
        sys.exit( 0 )

    # REMOVE ME: this is for testing
    def print_ports( self, name, lookup, ephemeral, message ):
        print("\n" + self.peer_name + " received " + name + "'s response:")
        print( "\t" + name + " lookup port: " + str( lookup ) )
        print(  "\t" + name + " ephemeral port: " + str( ephemeral ) )
        print(  "\t" + name + " message: " + message )
        print( "\n" )

################################################################################
################################ main ##########################################
################################################################################
if len( sys.argv ) == 5:  # first arg is the name of script
    my_peer = peer( sys.argv[ 1 ], sys.argv[ 2 ], int( sys.argv[ 3 ] ),
                    sys.argv[ 4 ] )
elif len( sys.argv ) == 7:  # first arg is the name of script
    my_peer = peer( sys.argv[ 1 ], sys.argv[ 2 ], int( sys.argv[ 3 ] ),
                    sys.argv[ 4 ], sys.argv[ 5 ], int( sys.argv[ 6 ] ) )
else:
    sys.exit( 0 )
################################################################################
############################## end main ########################################
###############################################################################