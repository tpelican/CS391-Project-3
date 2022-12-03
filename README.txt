Group:	Rudy Liljeberg & Thomas Pelegrin

How to Use:
	1. Open a terminal window inside of the project folder (or use an IDE to open the project; I prefer PyCharm, but any will work)
	2. If you are the first peer to be connecting in the network, type:
		python Peer.py <name> <ip> <lookup-port> <directory>
	3. Then, open a second terminal window. To connect this peer to an already exisiting peer, type:
		python Peer.py <name> <ip> <lookup-port> <directory> <peer-ip> <peer-lookup-port>
	4. After that, you may send and receive files from any peer on the network. You are given 4 commands to use:
		1. status  -  you can use status by typing '1', 's', or 'status'
			-> will give you the names, ip addresses, and lookup ports of all your peers

		2. find <filename>  -  you can use find by typing '2', 'f', or 'find <filename>'
			-> will do a local and network-wide search for a specific file

		3. get <filename> <target-ip> <targer-ftp>  -  you can use get get by typing '3', 'g', or 'get <args>'
			-> get will download a file from the specified peer

		4. quit  -  you can use quit by typing '4', 'q', or 'quit'
			-> will disconnect you from the network and notify your peers that you have disconnected

Unmet Requirements:	n/a
