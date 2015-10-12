class VolumeFilter():
    """ This is the default volume data filter. 
        Subclass this filter to transform the volume data.
    """
    name = 'Default'

    def filter(self, raw_data):
        """ Transform the volume data raw_data.
            Override this implementation to apply custom transformation.
        """
        return raw_data
