# Created as part of CS391 Project 3
# Professor: Dr. George Thomas
# date: 11/27/2022
class File_Table( dict ):
    def __init__( self ):
        """ Creates a new File_Table dictionary
        """
        super().__init__()
        self = dict()

    def add( self, file, dir_path, origin_peer ):
        """ Adds a new File key-value pair
        :param file: the name of the file
        :param dir_path: the peer this file is from
        :param origin_peer: the directory of the file
        :return: m/a
        """
        self[ file ] = dir_path, origin_peer
