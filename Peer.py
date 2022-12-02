import threading
import traceback
import sys, time, os
import Message_Table, Neighbor_Table, File_Table
import Udp_Message, Codes
from socket import *
from Message_Table import Message_Table
from Neighbor_Table import Neighbor_Table
from File_Table import File_Table
from Udp_Message import *
from Codes import Codes
from os.path import isfile, join
from datetime import datetime
from enum import Enum

################################################################################
################################################################################
# TODO: ========================================================================
#  - need to update the README.txt file once we are done
#  - I started working on the find method, not much is done, but almost all
#  of the pieces that are needed to do it are here already
#  - imports need to be cleaned up
#  - I'm note really sure what exactly the sequence number we need to have is
#   doing exactly -- seems pointless but meh I guess

# NOTE: ========================================================================
#  - I reworked the way that the UDP messages are sent back and forth. This
#  should make our lives a lot easier because we just need to create a
#  Udp_Message object now, pass in the arguments we need to send, and then do
#  msg.send()   -- let me know if there are any bugs with it


################################################################################
###                  		Peer class
################################################################################
class Peer:

    def __init__( self, name, ip, port, directory, peer_ip = None,
                  peer_port = None ):
        """ Creates a new Peer object
        :param name: the name of this Peer object
        :param ip: the ip of this Peer object
        :param port: the port of this Peer object
        :param directory: the directory of this Peer object
        :param peer_ip: the ip of a neighbor peer (a Peer object's peer)
        :param peer_port: the port of a neighbor peer (a Peer object's peer)
        """
        self.name = name
        self.ip = ip
        self.port = port
        self.directory = directory

        self.files = File_Table()
        self.neighbors = Neighbor_Table()
        self.file_requests = Message_Table()
        self.read_directory()

        self.active = True
        self.udp_lookup_socket = None
        self.tcp_file_transfer_socket = None

        self.lookup_port = port  # this is our UDP port
        self.file_transfer_port = self.lookup_port + 1  # TCP port

        self.setup_listener_sockets()  # sets up the tcp/udp listener sockets

        if peer_ip is not None and peer_port is not None:
            self.connect_to_neighbor( peer_ip, peer_port )

        self.command_menu()

    def setup_listener_sockets( self ):
        """ Sets up the udp lookup and tcp file transfer sockets
        :return: n/a
        """
        # --------- creates the udp lookup (listener) socket -----------------#
        self.udp_lookup_socket = socket( AF_INET, SOCK_DGRAM )
        # there is no connecting (handshaking) with UDP
        # the binding only needs to occur on the server, not the client
        # here we set the binding because we want a static port
        self.udp_lookup_socket.bind( (self.ip, self.port) )
        threading.Thread( target = self.udp_lookup_listener,
                          daemon = True ).start()
        # ---------------------------------------------------------------------#

        # --------- creates the tcp file transfer socket
        # ----------------------#
        self.tcp_file_transfer_socket = socket( AF_INET, SOCK_STREAM )
        # TCP handshaking
        # the binding only needs to occur on the server, not the client
        self.tcp_file_transfer_socket.bind( (self.ip, self.port) )
        self.tcp_file_transfer_socket.listen( 256 )  # connections queue size
        threading.Thread( target = self.tcp_file_listener,
                          daemon = True ).start()  #

    ############################################################################
    ###                  	establish neighbor connection
    ############################################################################
    def connect_to_neighbor( self, peer_ip, peer_port ):
        try:
            request = Udp_Message( code = Codes.PEER, src_name = self.name,
                                   src_ip = self.ip, src_port = self.port,
                                   dest_ip = peer_ip, dest_port = peer_port )
            response = request.send( accept_reply = True )
            peer_name = response.get_name()

            # FIXME: remove this -- for testing
            self.print_ports( self.name, peer_name, response.get_name(),
                              response.get_msg_content() )

            # add the neighbor response to the neighbors dictionary
            self.add_neighbor( peer_name, peer_ip, peer_port )
            self.print_connection_msg( peer_name, peer_ip, peer_port )

        except Exception as error:
            print( "\tA unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )

    # adds a neighbor to the neighbor dictionary
    def add_neighbor( self, peer_name, peer_ip, peer_port ):
        self.neighbors.add( peer_name, peer_ip, peer_port, 0)

    ############################################################################
    ###                 listens for incoming lookup requests
    ############################################################################
    def udp_lookup_listener( self ):
        """ Starts the lookup listener logic
        :return: n/a
        """
        print( "\t[UDP THREAD ACTIVE]\n" )

        while self.active:
            try:
                pass  # placeholder
                # do NOT have to accept since we are using UDP... I believe
                thread = threading.Thread( target = self.udp_lookup_handler,
                                           args =
                                           self.udp_lookup_socket.recvfrom(
                                               2048 ) )
                thread.start()  # starts the thread, start() calls run()

            except Exception as error:
                print( "\tA unknown critical error occurred" )
                print(
                    "\t" + str( error ) + "\n" + traceback.format_exc() +
                    "\n" )
                raise Exception()  # FIXME:

    def udp_lookup_handler( self, request, addr ):
        """ Handles the interactions coming in on the lookup port
        :param request: the sending Peer's message
        :param addr: the sending Peer's (ip, port) as tuple
        :return: n/a
        """
        try:
            # this is the message we got from the sender
            sender_msg = Udp_Message( response_msg = request.decode() )
            action_code = sender_msg.action_code()

            print( "Received:  " + sender_msg.to_string() )

            if action_code is Codes.ERROR:
                pass
            elif action_code is Codes.PEER:             # ACK
                self.peer_request_handler( sender_msg, addr )
            elif action_code is Codes.FIND:
                self.find_request_handler( sender_msg, addr )
            elif action_code is Codes.FOUND:
                print( "Sender has the file that you request: " )
                print( sender_msg )
            elif action_code is Codes.HERE:
                pass
            elif action_code is Codes.GET:
                pass
            elif action_code is Codes.QUIT:
                pass
            else:
                pass
        except Exception as error:
            print( "\n\tA unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
        finally:
            self.print_command_menu()

    def peer_request_handler( self, sender_msg, addr ):
        # this is the resposne we are sending back to the sender
        response = Udp_Message( code = Codes.PEER, src_name = self.name,
                                src_ip = self.ip, src_port = self.port,
                                dest_ip = addr[ 0 ],
                                dest_port = addr[ 1 ] )
        self.add_neighbor( sender_msg.get_name(),
                           sender_msg.get_src_ip(),
                           sender_msg.get_src_port() )
        self.print_acceptance_msg( sender_msg.get_name(),
                                   sender_msg.get_src_ip(),
                                   sender_msg.get_src_port() )
        response.send()

    def find_request_handler( self, sender_msg, addr ):
        print( "File request {0} received from {1}".format(
            sender_msg.file, sender_msg.get_name() ) )

        if self.file_requests.__contains__( (sender_msg.get_name(),
                                              sender_msg.seq) ):
            print("Duplicate; discarding.")
            return

        self.file_requests.add( sender_msg.get_name(),
                                sender_msg.seq )


        if self.files.__contains__( sender_msg.file ):
            dir_path, origin = self.files.get( sender_msg.file )
            print( "File " + sender_msg.file + " available on " +  dir_path )

            response = Udp_Message( code = Codes.FOUND, src_name = self.name,
                                    src_ip = self.ip, src_port = self.port,
                                    dest_ip = sender_msg.get_src_ip(),
                                    dest_port = sender_msg.get_src_port(),
                                    ftp = self.file_transfer_port )
            response.send()
        else:
            print("I made it to 225")
            self.forward_file_request( sender_msg.file, sender_msg )

        # self.read_directory()       # gets the most current directory
        # if self.files.__contains__( sender_msg.file ):
        #     pass
        # else:
        #     self.flood_peers( sender_msg.get_filename() )


    ############################################################################
    ###              listens for incoming file transfer requests
    ############################################################################
    def tcp_file_listener( self ):
        """ Starts the file transfer listener logic
        :return: n/a
        """
        print( "\t[TCP THREAD ACTIVE]\n" )

        while self.active:
            try:
                # have to accept() since we are using TCP
                thread = threading.Thread( target = self.tcp_file_handler,
                                           args =
                                           self.tcp_file_transfer_socket.accept() )
                thread.start()  # starts the thread, start() calls run()

            except Exception as error:
                print( "\tA unknown critical error occurred" )
                print(
                    "\t" + str( error ) + "\n" + traceback.format_exc() +
                    "\n" )

    def tcp_file_handler( self, tcp_socket, incoming_ip ):
        """ Handles the interactions from the tcp file transfer port
        :param tcp_socket:                  FIXME:
        :param incoming_ip:                 FIXME:
        :return: n/a
        """
        try:
            pass                # FIXME: needs to be implemented
            byte_string = tcp_socket.recv( 4096 ).decode()

        except Exception as error:
            print( "\tA unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )

    ############################################################################
    ###                         status method
    ############################################################################

    def status( self ):
        files_str = "Files: " + self.directory + "\n"
        peers_str = "Peers: \n"

        for peer_name, peer_data in self.neighbors.items():
            peers_str += "\t" + peer_name + " " + peer_addr[ 0 ] + ":" \
                         + str( peer_addr[ 1 ] ) + "\n"

        for file, origin_peer in self.files.items():
            files_str += "\t" + file + "\n"

        print( peers_str )
        print( files_str )

    ############################################################################
    ###                          find methods
    ############################################################################
    def read_directory( self ):
        """ Reads in this Peer's directory and adds each file to the File_Table
        :return: n/a
        """
        dir_files = os.listdir( self.directory )
        print( dir_files )
        for file in dir_files:
            self.files.add( file, self.directory, self.name )

    def find( self, filename, forward_request = None ):
        self.read_directory()     # updates the file directory w/ local files
        
        # print("'" + filename + "'")     # FIXME 

        if self.files.__contains__( filename ):
            dir_path, origin = self.files.get( filename )
            print( "File " + filename + " available on " + dir_path )
            self.files.get( filename )   # (dir, peer_origin)
        elif not forward_request is None:
            print( "File discovery in progress: Flooding" )
            self.flood_peers( filename )
        else:
            print("Flooding neighbors:")
            self.flood_peers( filename, forward_msg = forward_request )

    # sends back the original file request
    def forward_file_request( self, filename, message ):
        self.flood_peers( filename, forward_msg = message )

    def flood_peers( self, filename, forward_msg = None ):
        for peer_name, peer_data in self.neighbors.items():
            # if it's the same peer that it just got the message from, continue
            if forward_msg is not None and forward_msg.src_name == peer_name:
                continue
            
            print( "\tsending to " + peer_name )
            if forward_msg is None:
                self.neighbors.increment_seq( peer_name )
                peer_ip, peer_port, send_base = peer_data
                message = Udp_Message( code = Codes.FIND, src_name = self.name,
                                       src_ip = self.ip, src_port = self.port,
                                       dest_name = peer_name, dest_ip = 
                                       peer_ip, 
                                       dest_port = peer_port, seq = send_base,
                                       file = filename)
            else:
                message = forward_msg
            message.send()



    ############################################################################
    ###                          get methods
    ############################################################################
    def get( self ):
        pass            # part c, needs to be implemented

    def add_file( self, file, origin_peer ):
        """ Adds the name of the file to this Peer's File_Table
        :param file: the name of the file
        :param origin_peer: the original origin of the file
        :return: n/a
        """
        self.files.add( file, origin_peer )

    def get_files( self ):
        """ Returns the File_Table object
        :return: the File_Table object
        """
        return self.files

    ############################################################################
    ###                          quit methods
    ############################################################################
    def quit( self ):
        # needs to send messages to neighbors and attempt to close threads
        # safely
        self.udp_lookup_socket.close()
        self.tcp_file_transfer_socket.close()
        sys.exit( 0 )

    ############################################################################
    ###                       Utility methods
    ############################################################################
    def print_acceptance_msg( self, name, ip, port ):
        print( "\n\n{0}: Accepting {1} {2}:{3}\n".format( self.name, name, ip,
                                                          port ) )

    def print_connection_msg( self, name, ip, port ):
        print( "{0}: Connected {1} {2}:{3}\n".format( self.name, name, ip,
                                                      port ) )

    # REMOVE ME: this is for testing
    def print_ports( self, name, lookup, ephemeral, message ):
        print( self.name + " received " + name + "'s response: "
                                                 "\t\t\t\tFIXME: function is "
                                                 "for testing only" )
        print( "\t" + name + " lookup port: " + str( lookup ) )
        print( "\t" + name + " ephemeral port: " + str( ephemeral ) )
        print( "\t" + name + " message: " + message + "\n" )

    ############################################################################
    ###                           UI methods
    ############################################################################
    def command_menu( self ):
        """ Executes the command menu's logic
        :return: n/a
        """
        while self.active:
            self.print_command_menu()
            command = str( input() )
            # FIXME: need to parse the command string

            print( "" )  # prints a blank line

            if len( command ) <= 0:
                print( "No command listed." )
                continue

            if command[ 0 ] == 's':
                self.status()
            elif command[ 0 ] == 'f':
                print("Enter file: ")
                file = str( input() )       # FIXME: needs to parse command str
                self.find( file )
            elif command[ 0 ] == 'g':
                self.get()
            elif command[ 0 ] == 'q':
                print( "Peer terminated" )
                self.active = False
                time.sleep( 1 )  # delay to allow loops to finish and exit
                # safely if possible
                quit()
                break
            else:
                print( "Unknown command" )

    def print_command_menu( self ):
        """ Prints the command menu UI
        :return: n/a
        """
        print( "Your options:\n"
               "\t1. [s]tatus\n"
               "\t2. [f]ind <filename>\n"
               "\t3. [g]et <filename> <peer IP> <peer port>\n"
               "\t4. [q]uit\n"
               "Your choice: ", end = "" )


################################################################################
################################ main ##########################################
################################################################################
if len( sys.argv ) - 1 == 4:  # first arg is the name of script
    my_peer = Peer( sys.argv[ 1 ], sys.argv[ 2 ], int( sys.argv[ 3 ] ),
                    sys.argv[ 4 ] )
elif len( sys.argv ) - 1 == 6:  # first arg is the name of script
    my_peer = Peer( sys.argv[ 1 ], sys.argv[ 2 ], int( sys.argv[ 3 ] ),
                    sys.argv[ 4 ], sys.argv[ 5 ], int( sys.argv[ 6 ] ) )
else:
    sys.exit(
        0 )
################################################################################
############################## end main ########################################
###############################################################################
    # def create_response( self, code, name, ip, port ):
    #     """ Creates a new response message in the defined format
    #     :param code: the action code corresponding to the desired action
    #     :param name: the name of the Peer sending this response
    #     :param ip: the ip of the Peer sending this response
    #     :param port: the lookup port of the Peer sending this response
    #     :return: a formatted string in the response format
    #     """
    #     return "code={0} name={1} ip={2} port={3}\0".format( code, name, ip,
    #                                                          port )
    #
    # def read_lookup_response( self, response_message ):
    #     """ Parses the response string and returns the actual values
    #     :param response_message: the encoded response message from the Peer
    #     :return: a length 4 tuple (action_code, name, ip, port) from message
    #     """
    #     msg = response_message.decode()
    #     field_names = [ "code=", "name=", "ip=", "port=" ]
    #     field_values = [ ]
    #     i = 0
    #
    #     # if this is true, then the data has to be incorrect
    #     if len( msg ) <= 21:
    #         raise Error( "Received message is incomplete or corrupted" )
    #
    #     while i < 4 and msg.index( field_names[ i ] ) > -1:
    #         # this should be more robust                        FIXME:
    #         start = msg.index( field_names[ i ] ) + len( field_names[ i ] )
    #         if i < 3:
    #             end = msg.index( field_names[ i + 1 ], start )
    #         else:
    #             end = len( msg ) - 1
    #         field_values.append( msg[ start:end ].strip() )
    #
    #         # if start >= len( msg ) or end < 0:
    #         #     raise Error( "Received message is incomplete or corrupted" )
    #
    #         i += 1
    #     action_code = int( field_values[ 0 ] )
    #     name = str( field_values[ 1 ] )
    #     ip = str( field_values[ 2 ] )
    #     port = int( field_values[ 3 ] )
    #
    #     return action_code, name, ip, port