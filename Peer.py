import threading
import traceback
import sys, time, os

from socket import *
from os.path import isfile, join
from datetime import datetime

from Message_Table import Message_Table
from Neighbor_Table import Neighbor_Table
from File_Table import File_Table
from Message import Message
from Udp_Message import Udp_Message
from Tcp_Message import Tcp_Message
from Codes import Codes


################################################################################
################################################################################
# TODO: ========================================================================
#  - need to update the README.txt file once we are done
#  - I'm note really sure what exactly the sequence number we need to have is
#   doing exactly -- seems pointless but meh I guess
#  - I think the file send is supposed to be on an ephemeral port ??? ask>>
#  - when files are searched for, we need to use the directory to do it

# FIXME: need to fix the directory path stuff for files

# Created as part of CS391 Project 3
# Professor: Dr. George Thomas
# date: 11/27/2022
class Peer:
    """ Represents a single Peer in a P2P network """

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
        self.udp_lookup_socket.bind( (self.ip, self.port) )
        threading.Thread( target = self.udp_lookup_listener,
                          daemon = True ).start()

        # ---- creates the tcp file transfer (listener) socket ----------------#
        self.tcp_file_transfer_socket = socket( AF_INET, SOCK_STREAM )
        self.tcp_file_transfer_socket.bind( (self.ip, self.file_transfer_port) )
        self.tcp_file_transfer_socket.listen( 256 )  # connections queue size
        threading.Thread( target = self.tcp_file_listener,
                          daemon = True ).start()

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

            if action is Codes.PEER:  # ACK
                self.peer_request_handler( sender_msg, addr )
            elif action is Codes.FIND:
                self.find_request_handler( sender_msg )
            elif action is Codes.FOUND:
                # this is what gets printed when the requester gets back a found
                # message
                print( "\nFile is available at peer => ({0}, {1}, {2}, {3}"
                       ")\n".format( sender_msg.get_name(),
                                     sender_msg.get_src_ip(),
                                     sender_msg.get_src_port(),
                                     sender_msg.get_ftp() ) )

            elif action is Codes.QUIT:
                self.delete_peer( sender_msg.get_name() )
            else:
                pass  # print out error since we received one
        except Exception as error:
            print( "\n\tAn unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )

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

            self.read_directory()  # updates the directory

            if action is Codes.ERROR or (
                    Codes.GET and not self.files.__contains__( filename )):
                print( "\nError: no such file\n" )
                self.send_error( sender_socket, request )

            elif action is Codes.GET:
                # this peer received a request to GET a file,
                # so this peer SENDS a file to satisfy the GET request
                self.send_file( sender_socket, request )
            else:
                print( "\nUnknown action\n" )
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

        response.send_file( sender_socket, self.directory )

    def receive_file( self, request, connect_socket ):
        """ Receives a file being sent from the tcp socket connect_socket
        :param request: the SEND message from the sender
        :param connect_socket: the socket that is being used
        :return: n/a
        """
        file = open( os.path.join( self.directory,
                                   request.get_filename() ), "wb" )
                                                         # wb =  write bytes
        try:
            data = connect_socket.recv( 1024 )
            while data:  # loop executes until there is no more data left
                file.write( data )
                data = connect_socket.recv( 1024 )

            self.files.add( request.get_filename(), self.directory,
                            request.get_name() )
            print( "\nFile received\n" )
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
    def get( self, filename, target_ip, target_ftp ):
        connect_socket = socket( AF_INET, SOCK_STREAM )
        connect_socket.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )
        try:
            target_name = ""
            for peer_name, peer_data in self.neighbors.items():
                peer_ip, peer_port, send_base = peer_data

                if peer_ip == target_ip:
                    target_name = peer_name

            if target_name == "":
                print( "\nNo peer with address ({0}, {1}) was found.".format(
                    target_ip, target_ftp ) )
                return
            connect_socket.connect( (target_ip, target_ftp) )

            # sends tcp msg to the ftp port of the target using the new socket
            # sending GET request to the target
            request = Tcp_Message( code = Codes.GET, src_name = self.name,
                                   src_ip = self.ip, file = filename,
                                   dest_name = target_name,
                                   dest_ip = target_ip,
                                   ftp = target_ftp )
            connect_socket.send( request.codify() )

            # receives the SEND or ERROR response from the target, indicating
            # whether the file was found and able to be sent
            response = connect_socket.recv( 2048 )
            request = Tcp_Message( response_msg = response.decode() )
            action = request.action_code()

            if action is Codes.SEND:
                ready = Tcp_Message( code = Codes.READY, src_name = self.name,
                                     src_ip = self.ip, file = filename,
                                     dest_name = target_name,
                                     dest_ip = target_ip,
                                     ftp = target_ftp )
                connect_socket.send( ready.codify() )

                self.receive_file( request, connect_socket )
            else:
                print( "\nError: no such file\n" )
        except Exception as error:
            print( "\tAn unknown critical error occurred" )
            print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
        finally:
            connect_socket.close()

    ############################################################################
    ###                         status method
    ############################################################################
    def status( self ):
        """ Prints a formatted list of peers and files
        :return: n/a
        """
        peers_str = "\nPeers: \n"
        files_str = "Files: " + self.directory + "\n"

        for peer_name, peer_data in self.neighbors.items():
            peers_str += "\t" + peer_name + " " + peer_data[ 0 ] + ":" + str(
                peer_data[ 1 ] ) + "\n"
        for file, origin_peer in self.files.items():
            files_str += "\t" + file + "\n"

        print( peers_str )
        print( files_str )

    ############################################################################
    ###                        find & file methods
    ############################################################################
    def read_directory( self ):
        """ Reads in this Peer's directory and adds each file to the File_Table
        :return: n/a
        """
        dir_files = os.listdir( self.directory )
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
            print( "\nDuplicate; discarding." )
            return
        self.file_requests.add( sender_msg.get_name(), sender_msg.seq )

        if self.files.__contains__( sender_msg.file ):
            dir_path, origin = self.files.get( sender_msg.file )
            print( "\nFile " + sender_msg.file + " available on "
                   + dir_path + "" )

            response = Udp_Message( code = Codes.FOUND, src_name = self.name,
                                    src_ip = self.ip, src_port = self.port,
                                    dest_ip = sender_msg.get_src_ip(),
                                    dest_port = sender_msg.get_src_port(),
                                    file = sender_msg.get_filename(),
                                    ftp = self.file_transfer_port )
            response.send()
        else:
            self.forward_file_request( sender_msg.file, sender_msg )

    def find( self, filename, forward_request = None ):
        """ Attempts to find the requested file, first locally,  then flooding
        :param filename: the name of the file
        :param forward_request: whether this peer is forwarding a request
        :return: n/a
        """
        self.read_directory()  # updates the file directory w/ local files

        if self.files.__contains__( filename ):  # if file is locally found
            dir_path, origin = self.files.get( filename )
            print( "\nFile " + filename + " available on " + dir_path )
            self.files.get( filename )  # (dir, peer_origin)
        elif forward_request is None:  # if this is a not a forwarded FIND
            print( "\nFile discovery in progress: Flooding" )
            self.flood_peers( filename )
        else:  # otherwise, flood all peers
            print( "\nFlooding to neighbors:" )
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
            print( "\tsending to " + peer_name )

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
        self.active = False

        for peer_name, peer_data in self.neighbors.items():
            peer_ip, peer_port, send_base = peer_data
            print( "\nNotifying " + peer_name + " of departure" )

            message = Udp_Message( code = Codes.QUIT, src_name = self.name,
                                   src_ip = self.ip, src_port = self.port,
                                   dest_name = peer_name, dest_ip = peer_ip,
                                   dest_port = peer_port )
            message.send()
        self.udp_lookup_socket.close()
        self.tcp_file_transfer_socket.close()

        print( "Quitting" )
        sys.exit( 0 )

    def delete_peer( self, peer_name ):
        """ Removes the peer that quit the network
        :param peer_name: the name of the peer
        :return: n/a
        """
        self.neighbors.pop( peer_name )
        print( "\n" + peer_name + " is offline" )

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
        print( "{0}: Connected {1} {2}:{3}\n".format(
            self.name, name, ip, port ) )

    ############################################################################
    ###                           UI methods
    ############################################################################
    def command_menu( self ):
        """ Executes the command menu's logic
        :return: n/a
        """
        while self.active:
            self.print_command_menu()
            args = str( input() ).strip().split( " " )
            command = args[ 0 ]

            if len( command ) <= 0:
                print( "" )
                continue

            if command[ 0 ] == 's' or command[ 0 ] == '1' \
                    or "status" in command:
                self.status()
            elif (command[ 0 ] == 'f' or command[ 0 ] == '2'
                  or "find" in command) and len( args ) > 1:
                self.find( args[ 1 ] )
            elif (command[ 0 ] == 'g' or command[ 0 ] == '3'
                  or "get" in command) and len( args ) > 3:
                self.get( args[ 1 ], args[ 2 ], int( args[ 3 ] ) )
            elif command[ 0 ] == 'q' or command[ 0 ] == '4' \
                    or "quit" in command:
                self.quit()
            else:
                print( "Unknown command" )

            time.sleep( 1 )

    def print_command_menu( self ):
        """ Prints the command menu UI
        :return: n/a
        """
        print( "Your options:\n"
               "\t1. [s]tatus\n"
               "\t2. [f]ind <filename>\n"
               "\t3. [g]et <filename> <target-peer-ip> "
               "<target-file-transfer-port>\n"
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
    print( "Invalid number of peer arguments" )
    sys.exit( 0 )
################################################################################
############################## end main ########################################
###############################################################################