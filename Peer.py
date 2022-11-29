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
#  - a lot of this should probably be refactored into different files, but I'm
#       leaving it as is right now because it's easier to work with atm

# NOTE: ========================================================================
#  - when printing print("") it will by default print a new line, so doing
#		print("\n") will print 2 new lines etc

# MESSAGE FORMAT:  code={0} name={1} ip={2} port={3}
# Action Codes:                                         (for now)
#   0 - error
#   1 - add peer
#   2 - file inquiry request
#   3 - file download request

################################################################################
###                  		file table class
################################################################################
class File_Table( dict ):
	def __init__( self ):
		""" Creates a new File_Table dictionary
		"""
		super().__init__()
		self = dict()

	def add( self, file, origin_peer ):
		""" Adds a new File key-value pair
		:param file: the name of the file
		:param origin_peer: the peer this file is from
		:return: m/a
		"""
		self[ file ] = file, origin_peer


################################################################################
###                  	  Neighbors table class
################################################################################
class Neighbor_Table( dict ):
	def __init__( self ):
		""" Creates a new Neighbor_Table dictionary
		"""
		super().__init__()
		self = dict()

	def add( self, peer_name, peer_ip, peer_port ):
		""" Adds a new Neighbor key-value pair
		:param peer_name: the name of the neighboring peer
		:param peer_ip: the ip of the neighboring peer
		:param peer_port: the lookup port of the neighboring peer
		:return: n/a
		"""
		self[ peer_name ] = peer_ip, peer_port


################################################################################
###                  		Peer class
################################################################################
class Peer:
	def command_menu( self ):
		""" Executes the command menu's logic
		:return: n/a
		"""
		while self.active:
			self.print_command_menu()
			command = str( input() )
			print("")				# prints a blank line

			if len( command ) <= 0:
				print("No command listed.")
				continue

			if command[ 0 ] == 's':
				self.status()
			elif command[ 0 ] == 'f':
				self.find()
			elif command[ 0 ] == 'g':
				one = 1  # get()
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

	# ---------------------------------------------------------------------#

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

	############################################################################
	###                  	establish neighbor connection
	############################################################################
	def connect_to_neighbor( self, peer_ip, peer_port ):
		udp_ephemeral = socket( AF_INET, SOCK_DGRAM )

		# I don't think this method needs to be on its own thread since it
		# only executes once
		# I think this line only gets used in TCP               FIXME:*******
		udp_ephemeral.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )

		# tcp.setsockopt( SOL_SOCKET, SO_REUSEADDR, 1 )  ******* REMOVE
		# udp_ephemeral.listen( 256 )  # connections queue size
		try:
			new_neighbor_request = self.create_response( 1, self.name, self.ip,
				self.port )
			udp_ephemeral.sendto( new_neighbor_request.encode(),
				(peer_ip, peer_port) )

			# will receive a name of 256 characters, we only need to receive
			# the name here since that's all that needs to be sent at this
			# stage
			peer_name, addr = udp_ephemeral.recvfrom( 2048 )

			# FIXME: remove this -- for testing
			self.print_ports( peer_name.decode(), peer_port, str( addr[ 1 ] ),
				peer_name.decode() )

			# add the neighbor response to the neighbors dictionary
			self.add_neighbor( peer_name.decode(), peer_ip, peer_port )
			self.print_connection_msg( peer_name.decode(), peer_ip, peer_port )

		except Exception as error:
			print( "\tA unknown critical error occurred" )
			print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )
		finally:
			udp_ephemeral.close()
			return

	# adds a neighbor to the neighbor dictionary
	def add_neighbor( self, peer_name, peer_ip, peer_port ):
		self.neighbors.add( peer_name, peer_ip, peer_port )

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
					args = self.udp_lookup_socket.recvfrom( 256 ) )
				thread.start()  # starts the thread, start() calls run()

			except Exception as error:
				print( "\tA unknown critical error occurred" )
				print(
					"\t" + str( error ) + "\n" + traceback.format_exc() +
					"\n" )
				raise Exception()  # FIXME:

	def udp_lookup_handler( self, sender_msg, sender_address ):
		""" Handles the interactions coming in on the lookup port
		:param sender_msg: the sending Peer's message
		:param sender_address: the sending Peer's ip
		:return: n/a
		"""
		# UDP needs to have enough space in the buffer to receive, otherwise
		# the packet will be dropped
		try:
			# (byte_str, sender_ip) = self.udp_lookup_socket.recvfrom( 4096
			# ).decode()
			# data is the byte string

			# FIXME: do not actually need the sender ip in the repsonse msg

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
				msg = self.name
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
			sock.close()  # don't need to close with UDP?
		except Exception as error:
			print( "\n\tA unknown critical error occurred" )
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
		print( "\t[TCP THREAD ACTIVE]\n" )

		while self.active:
			try:
				# have to accept() since we are using TCP
				thread = threading.Thread( target = self.tcp_file_handler,
					args = self.tcp_file_transfer_socket.accept() )
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
			byte_string = tcp_socket.recv( 4096 ).decode()

		except Exception as error:
			print( "\tA unknown critical error occurred" )
			print( "\t" + str( error ) + "\n" + traceback.format_exc() + "\n" )

	############################################################################
	###                         Mandatory methods
	############################################################################
	def status( self ):
		files_str = "Files: " + self.directory + "\n"
		peers_str = "Peers: \n"

		for peer_name, peer_addr in self.neighbors.items():
			peers_str += "\t" + peer_name + " " + peer_addr[ 0 ] + ":" \
						 + str(peer_addr[ 1 ]) + "\n"

		for file, origin_peer in self.files.items():
			files_str += "\t" + file + "\n"

		print( peers_str );
		print( files_str )

	def send_file( self, peer_name, peer_ip, peer_port, directory,
			recv_peer_ip,
			recv_peer_port ):
		if recv_peer_ip is None:
			recv_peer_ip = -1
		if recv_peer_port is None:
			recv_peer_port = -1
		one = 1

	def read_directory( self ):
		""" Reads in this Peer's directory and adds each file to the File_Table
		:return: n/a
		"""
		dir_files = os.listdir( self.directory )
		print( dir_files )
		for file in dir_files:
			self.files.add( file, self.name )

	def get_files( self ):
		""" Returns the File_Table object
		:return: the File_Table object
		"""
		return self.files

	def add_file( self, file, origin_peer ):
		""" Adds the name of the file to this Peer's File_Table
		:param file: the name of the file
		:param origin_peer: the original origin of the file
		:return: n/a
		"""
		self.files.add( file, origin_peer )

	############################################################################
	###                       Utility methods
	############################################################################

	# returns an encoded response -- note the null terminating character
	def create_response( self, code, name, ip, port ):
		""" Creates a new response message in the defined format
		:param code: the action code corresponding to the desired action
		:param name: the name of the Peer sending this response
		:param ip: the ip of the Peer sending this response
		:param port: the lookup port of the Peer sending this response
		:return: a formatted string in the response format
		"""
		return "code={0} name={1} ip={2} port={3}\0".format( code, name, ip,
			port )

	def read_lookup_response( self, response_message ):
		""" Parses the response string and returns the actual values
		:param response_message: the encoded response message from the Peer
		:return: a length 4 tuple (action_code, name, ip, port) from message
		"""
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
		print(
			"\n\n{0}: Accepting {1} {2}:{3}\n".format( self.name, name, ip,
				port ) )

	def print_connection_msg( self, name, ip, port ):
		print(
			"{0}: Connected {1} {2}:{3}\n".format( self.name, name, ip,
				port ) )

	def quit( self ):
		# needs to send messages to neighbors and attempt to close threads
		# safely
		self.udp_lookup_socket.close()
		self.tcp_file_transfer_socket.close()
		sys.exit( 0 )

	# REMOVE ME: this is for testing
	def print_ports( self, name, lookup, ephemeral, message ):
		print( self.name.strip() + " received " + name + "'s response:" )
		print( "\t" + name + " lookup port: " + str( lookup ) )
		print( "\t" + name + " ephemeral port: " + str( ephemeral ) )
		print( "\t" + name + " message: " + message  + "\n")

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
