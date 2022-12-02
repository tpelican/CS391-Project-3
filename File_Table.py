################################################################################
###                  		file table class
################################################################################
class File_Table( dict ):
    def __init__( self ):
        """ Creates a new File_Table dictionary
        """
        super().__init__()
        self = dict()

    # FIXME: may also want to include the directory path
    def add( self, file, direct, dir_path ):
        """ Adds a new File key-value pair
        :param file: the name of the file
        :param direct: the directory of the file
        :param dir_path: the peer this file is from
        :return: m/a
        """
        self[ file ] = direct, dir_path
