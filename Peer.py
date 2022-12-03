import threading
import traceback
import sys, time, os

from socket import *
from Message_Table import Message_Table
from Neighbor_Table import Neighbor_Table
from File_Table import File_Table

from Message import Message
from Udp_Message import Udp_Message
from Tcp_Message import Tcp_Message
from Codes import Codes
from os.path import isfile, join
from datetime import datetime
from enum import Enum


################################################################################
################################################################################
# TODO: ========================================================================
#  - the quit method needs to inform peers, needs testing with 3+ peers,
#       print messages need to be verified per document, and need to clean
#  - resolve FIXME: comments
#  - need to update the README.txt file once we are done
#  - I'm note really sure what exactly the sequence number we need to have is
#   doing exactly -- seems pointless but meh I guess
#  - I think the file send is supposed to be on an ephemeral port ??? ask>>
#  - when files are searched for, we need to use the directory to do it


# Created as part of CS391 Project 3
# Professor: Dr. George Thomas
# date: 11/29/2022
class Peer:
    """ Represents a single peer in a P2P network """
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

        # --------- creates the tcp file transfer socket ----------------------#
        self.tcp_file_transfer_socket = socket( AF_INET, SOCK_STREAM )
        # TCP handshaking
        # the binding only needs to occur on the server, not the client
        self.tcp_file_transfer_socket.bind( (self.ip, self.file_transfer_port) )
        self.tcp_file_transfer_socket.listen( 256 )  # connections queue size
        threading.Thread( target = self.tcp_file_listener,
                          daemon = True ).start()  #

    ############################################################################
    ###                  	establish neighbor connection
    ############################################################################
    def connect_to_neighbor( self, peer_ip, peer_port ):
        """ Connects this Peer to another peer as a neighbor
        :param peer_ip: the ip of the peer 
        :param peer_port: the port of the peer
        :return: n/a
        """
        try:
            request = Udp_Message( code = Codes.PEER, src_name = self.name,
                                   src_ip = self.ip, src_port = self.port,
                                   dest_ip = peer_ip,
                                   dest_port = peer_port )
            response = request.send( accept_reply = True )
            peer_name = response.get_name()

            # add the neighbor response to the neighbors dictionary
            self.add_neighbor( peer_name, peer_ip, peer_port )
            self.print_connection_msg( peer_name, peer_ip, peer_port )
        except Exception as error:
            print( "\tAn unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )

    # adds a neighbor to the neighbor dictionary
    def add_neighbor( self, peer_name, peer_ip, peer_port ):
        """ Adds the peer with a default seq number of 0
        :param peer_name: the name of the peer
        :param peer_ip: the ip of the peer
        :param peer_port: the port of the peer
        :return: n/a
        """
        self.neighbors.add( peer_name, peer_ip, peer_port, 0 )

    ############################################################################
    ###                 listens for incoming lookup requests
    ############################################################################
    def udp_lookup_listener( self ):
        """ Starts the lookup listener logic
        :return: n/a
        """
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
                print( "\tAn unknown critical error occurred" )
                print(
                    "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
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
            action = sender_msg.action_code()

            print( "Received:  " + sender_msg.to_string() )

            if action is Codes.ERROR:
                pass
            elif action is Codes.PEER:  # ACK
                self.peer_request_handler( sender_msg, addr )
            elif action is Codes.FIND:
                self.find_request_handler( sender_msg )
            elif action is Codes.FOUND:  # FIXME:
                print( "File " + sender_msg.file + " available on "
                       + dir_path + "\n" )
            elif action is Codes.QUIT:
                self.quit()  # FIXME: needs implementation
            else:
                pass
        except Exception as error:
            print( "\n\tAn unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
        finally:
            self.print_command_menu()

    ############################################################################
    ###              listens for incoming file transfer requests
    ############################################################################
    def tcp_file_listener( self ):
        """ Starts the file transfer listener logic
        :return: n/a
        """
        while self.active:
            try:
                thread = threading.Thread( target = self.tcp_file_handler,
                                           args =
                                           self.tcp_file_transfer_socket.accept() )
                thread.start()

            except Exception as error:
                print( "\tAn unknown critical error occurred" )
                print(
                    "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )

    def tcp_file_handler( self, sender_socket, sender_addr ):
        """ Handles the interactions from the tcp file transfer port
        :param sender_socket: the socket that was used by the sender
        :param sender_addr: the (ip, port) of the sending peer
        :return: n/a
        """
        try:
            request = Tcp_Message(
                response_msg = sender_socket.recv( 2048 ).decode() )
            action = request.action_code()
            filename = request.get_filename()

            self.read_directory()       # updates the directory

            if action is Codes.ERROR or (
                    Codes.GET and not self.files.__contains__( filename )):
                print( "Error: no such file" )
                self.send_error( sender_socket, request )

            elif action is Codes.GET:
                # this peer received a request to GET a file,
                # so this peer SENDS a file to satisfy the GET request
                self.send_file( sender_socket, request )
            else:
                print("Unknown action")
        except Exception as error:
            print( "\tAn unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )

    def send_file( self, sender_socket, request ):
        print( "Received request for {0} from {1}".format(
            request.get_filename(), request.get_name() ) )

        # preface message containing file information
        response = Tcp_Message( code = Codes.SEND, src_name = self.name,
                                dest_ip = request.get_src_ip(),
                                file = request.get_filename(),
                                ftp = request.get_ftp() )
        sender_socket.send( response.codify() )

        # wait to receive READY from the requesting peer
        sender_socket.recv( 2048 ).decode()
        
        response.send_file( sender_socket )

    def receive_file( self, request, connect_socket ):
        """ Receives a file being sent from the tcp socket connect_socket
        :param request: the SEND message from the sender
        :param connect_socket: the socket that is being used
        :return: n/a
        """
        file = open( request.get_filename(), "wb" )  # wb = write bytes
        try:
            data = connect_socket.recv( 1024 )
            while data:  # loop executes until there is no more data left
                file.write( data )
                data = connect_socket.recv( 1024 )

            self.files.add( request.get_filename(), self.directory,
                            request.get_name() )
            # emp_socket.shutdown( SHUT_RD )
        except Exception as error:
            print( "\tAn unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
        finally:
            file.close()

    def send_error( self, sender_socket, request ):
        """ Sends back an error message to the peer who request the file
        :param sender_socket:
        :param request:
        :return: n/a
        """
        response = Tcp_Message( code = Codes.ERROR, src_name = self.name,
                                dest_ip = request.get_src_ip(),
                                file = request.get_filename(),
                                ftp = request.get_ftp() )
        sender_socket.send( response.codify() )

    ############################################################################
    ###                          get methods
    ############################################################################
    def get( self, filename, target_ip, target_name ):
        # self.tcp_file_transfer_socket.connect( (target_ip, target_ftp) )
        emp_socket = socket( AF_INET, SOCK_STREAM )
        emp_socket.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )
        try:
            if not self.neighbors.__contains__( target_name ):
                print( "No peer by the name of "
                       + target_name + " was found. " )
                return
            peer_ip, peer_port, send_base = self.neighbors.get( target_name )
            emp_socket.connect( (peer_ip, peer_port + 1) )

            # sends tcp msg to the ftp port of the target using the new socket
            # sending GET request to the target
            request = Tcp_Message( code = Codes.GET, src_name = self.name,
                                   src_ip = self.ip, file = filename,
                                   dest_name = target_name,
                                   dest_ip = target_ip,
                                   ftp = int( peer_port ) + 1 )
            emp_socket.send( request.codify() )

            # receives the SEND or ERROR response from the target, indicating
            # whether the file was found and able to be sent
            response = emp_socket.recv( 2048 )
            request = Tcp_Message( response_msg = response.decode() )
            action = request.action_code()

            if action is Codes.SEND:

                # FIXME: need to change the peer_port + 1, to actually use the
                # ftp port specified

                ready = Tcp_Message( code = Codes.READY, src_name = self.name,
                                   src_ip = self.ip, file = filename,
                                   dest_name = target_name,
                                   dest_ip = target_ip,
                                   ftp = int( peer_port ) + 1 )
                emp_socket.send( ready.codify() )

                self.receive_file( request, emp_socket )
            else:
                print( "Error: no such file" )
        except Exception as error:
            print( "\tAn unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
        finally:
            emp_socket.close()

    ############################################################################
    ###                         status method
    ############################################################################
    def status( self ):
        """ Prints a formatted list of peers and files
        :return: n/a
        """
        files_str = "Files: " + self.directory + "\n"
        peers_str = "Peers: \n"

        for peer_name, peer_data in self.neighbors.items():
            peers_str += "\t" + peer_name + " " + peer_data[ 0 ] + ":" + str(
                peer_data[ 1 ] ) + "\n"
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
        print( dir_files )  # FIXME: remove this
        for file in dir_files:
            self.files.add( file, self.directory, self.name )

    def peer_request_handler( self, sender_msg, addr ):
        """ Handles requests to create a 'peer' (neighbor) connection
        :param sender_msg: the peer request message
        :param addr: the address tuple (ip, port)
        :return: n/a
        """
        # this is the response we are sending back to the sender
        response = Udp_Message( code = Codes.PEER, src_name = self.name,
                                src_ip = self.ip, src_port = self.port,
                                dest_ip = addr[ 0 ],
                                dest_port = addr[ 1 ] )

        self.add_neighbor( sender_msg.get_name(), sender_msg.get_src_ip(),
                           sender_msg.get_src_port() )
        self.print_acceptance_msg( sender_msg.get_name(),
                                   sender_msg.get_src_ip(),
                                   sender_msg.get_src_port() )
        response.send()

    def find_request_handler( self, sender_msg ):
        """ Handles the FIND file requests sent from peers
        :param sender_msg: the FIND message that was sent from the peer
        :return: n/a
        """
        print( "File request {0} received from {1}".format(
            sender_msg.file, sender_msg.get_name() ) )

        if self.file_requests.__contains__(
                (sender_msg.get_name(), sender_msg.seq) ):
            print( "Duplicate; discarding." )
            return

        self.file_requests.add( sender_msg.get_name(), sender_msg.seq )

        if self.files.__contains__( sender_msg.file ):
            dir_path, origin = self.files.get( sender_msg.file )
            print( "File " + sender_msg.file + " available on "
                   + dir_path + "\n" )

            response = Udp_Message( code = Codes.FOUND, src_name = self.name,
                                    src_ip = self.ip, src_port = self.port,
                                    dest_ip = sender_msg.get_src_ip(),
                                    dest_port = sender_msg.get_src_port(),
                                    ftp = self.file_transfer_port )
            response.send()
        else:
            self.forward_file_request( sender_msg.file, sender_msg )

    def find( self, filename, forward_request = None ):
        self.read_directory()  # updates the file directory w/ local files

        if self.files.__contains__( filename ): # if file is locally found
            dir_path, origin = self.files.get( filename )
            print( "File " + filename + " available on " + dir_path )
            self.files.get( filename )  # (dir, peer_origin)
        elif not forward_request is None:  # if this is a not a forwarded FIND
            print( "File discovery in progress: Flooding" )
            self.flood_peers( filename )
        else:                               # otherwise, flood all peers
            print( "Flooding neighbors:" )
            self.flood_peers( filename, forward_msg = forward_request )

    def forward_file_request( self, filename, message ):
        """ Forwards the received file request to this Peer's peers
        :param filename: the name of the file
        :param message: the UDP message to forward
        :return: n/a
        """
        self.flood_peers( filename, forward_msg = message )

    def flood_peers( self, filename, forward_msg = None ):
        """ Floods the neighboring peers with a FIND request
        :param filename: the name of the file
        :param forward_msg: provided if the msg has been forwarded to this peer
        :return: n/a
        """
        for peer_name, peer_data in self.neighbors.items():
            # if it's the same peer that it just got the message from, skip
            if forward_msg is not None and forward_msg.src_name == peer_name:
                continue

            if forward_msg is None:
                self.neighbors.increment_seq( peer_name )
                peer_ip, peer_port, send_base = peer_data
                message = Udp_Message( code = Codes.FIND, src_name = self.name,
                                       src_ip = self.ip, src_port = self.port,
                                       dest_name = peer_name, dest_ip = peer_ip,
                                       dest_port = peer_port, seq = send_base,
                                       file = filename )
            else:
                message = forward_msg
            message.send()

    ############################################################################
    ###                          quit methods
    ############################################################################
    def quit( self ):
        """ Notifies peers that this peer is disconnecting and shuts down
        :return: n/a
        """

        ### FIXME: need to send out a "remove me" message
        
        self.udp_lookup_socket.close()
        self.tcp_file_transfer_socket.close()
        sys.exit( 0 )

    ############################################################################
    ###                         print methods
    ############################################################################
    def print_acceptance_msg( self, name, ip, port ):
        """ Prints that the peer request was accepted
        :param name: the name of the peer
        :param ip: the ip of the peer
        :param port: the port of the peer
        :return: n/a
        """
        print( "\n\n{0}: Accepting {1} {2}:{3}\n".format( 
            self.name, name, ip, port ) )

    def print_connection_msg( self, name, ip, port ):
        """ Prints that the peer was successfully 'peered' with neighbor peer
        :param name: the name of the peer
        :param ip: the ip of the peer
        :param port: the port of the peer
        :return: n/a
        """
        print("{0}: Connected {1} {2}:{3}\n".format( 
            self.name, name, ip, port ) )

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

            if command[ 0 ] == 's' or "status" in command:
                self.status()
            elif command[ 0 ] == 'f' or "find" in command:
                print( "Enter file: " )
                file = str( input() )  # FIXME: needs to parse command str
                self.find( file )
            elif command[ 0 ] == 'g' or "get" in command:
                # print("Filename: ")
                # file = str( input() )
                # 
                # print("Target ip: ")
                # target_ip = str( input() )
                # 
                # print( "Peer name: " )
                # peer_name = str( input() )
                file = "send_me.txt"
                target_ip = "localhost"
                peer_name = "A"

                self.get( file, target_ip, peer_name )
            elif command[ 0 ] == 'q' or "quit" in command:
                print( "Peer terminated" )
                self.active = False
                time.sleep( 1 )  # delay to allow everything time to close up
                quit()
            else:
                print( "Unknown command" )

    def get_command( self, raw_input ):
        user_input = raw_input.split(" ")   # split into list at space

        command = user_input[ 0 ]  # every thing else in the list are arguments

        if command[ 0 ] == 's' or "status" in command:
            pass
        elif command[ 0 ] == 'f' or "find" in command:
            pass
        elif command[ 0 ] == 'g' or "get" in command:
            pass
        elif command[ 0 ] == 'q' or "quit" in command:
            pass
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
    sys.exit( 0 )
################################################################################
############################## end main ########################################
###############################################################################