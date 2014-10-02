import numpy as np

from traits.api import HasTraits, Any, Array, Float, Property, Tuple
from tvtk.api import tvtk


class VolumeData(HasTraits):
    """ The volume image data.
    """

    # The data itself.
    raw_data = Property(Array(shape=(None, None, None)))

    # The data as a fortran array
    _raw_data = Array(shape=(None, None, None))

    # The bounds of the volume
    bounds = Tuple(Float, Float, Float)

    # The spacing between grid points in each dimension.
    spacing = Tuple(Float, Float, Float)

    # The TVTK ImageData for the volume.
    image_data = Any()

    # A resampled version of the data
    resampled_image_data = Any()

    def _bounds_default(self):
        return tuple(np.array(self.spacing) * np.array(self.raw_data.shape))

    def _spacing_default(self):
        return (1.0, 1.0, 1.0)

    def _image_data_default(self):
        image_data = tvtk.ImageData()
        image_data.spacing = self.spacing
        image_data.dimensions = self.raw_data.shape
        image_data.point_data.scalars = self.raw_data.ravel('F')
        # The point data scalars need a name for some Mayavi operations.
        image_data.point_data.scalars.name = 'VolumeData'

        return image_data

    def _resampled_image_data_default(self):
        image_data = self.image_data
        spacing = image_data.spacing
        dims = image_data.dimensions
        output_spacing = (spacing[0] * (dims[0] / 256.0),
                          spacing[1] * (dims[1] / 256.0),
                          spacing[2] * (dims[2] / 256.0))
        reslicer = tvtk.ImageReslice(input=image_data,
                                     interpolation_mode='cubic',
                                     output_extent=(0, 255, 0, 255, 0, 255),
                                     output_spacing=output_spacing)
        reslicer.update()
        result = reslicer.output
        result.point_data.scalars.name = 'VolumeData'
        return reslicer.output

    def _get_raw_data(self):
        return self._raw_data

    def _set_raw_data(self, value):
        self._raw_data = np.asfortranarray(value)
