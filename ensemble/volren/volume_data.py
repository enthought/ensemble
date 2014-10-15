import numpy as np

from traits.api import HasTraits, Array, Float, Instance, Property, Tuple
from tvtk.api import tvtk


ThreeDeeArray = Array(shape=(None, None, None))

# The point data scalars need a name for some Mayavi operations.
POINT_DATA_SCALARS_NAME = 'VolumeData'


def _apply_mask(volume_data, mask_data):
    """ Mask out a portion of the data.
    """
    mask_image_data = _image_data_from_array(mask_data, volume_data.spacing)
    masker = tvtk.ImageMask()
    masker.set_image_input(volume_data)
    masker.set_mask_input(mask_image_data)
    masker.update()
    result = masker.output
    result.point_data.scalars.name = POINT_DATA_SCALARS_NAME
    return masker.output


def _image_data_from_array(array, spacing):
    """ Build an ImageData object from a numpy array.
    """
    image_data = tvtk.ImageData()
    image_data.spacing = spacing
    image_data.dimensions = array.shape
    image_data.point_data.scalars = array.ravel('F')
    image_data.point_data.scalars.name = POINT_DATA_SCALARS_NAME

    return image_data


def _resample_data(image_data):
    """ Resample data onto a uniform 256^3 grid.
    """
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
    result.point_data.scalars.name = POINT_DATA_SCALARS_NAME
    return reslicer.output


class VolumeData(HasTraits):
    """ The volume image data.
    """

    # A mask to apply to the data
    mask_data = Property(ThreeDeeArray)

    # The mask data as a fortran array
    _mask_data = ThreeDeeArray

    # The data itself.
    raw_data = Property(ThreeDeeArray)

    # The data as a fortran array
    _raw_data = ThreeDeeArray

    # The bounds of the volume
    bounds = Tuple(Float, Float, Float)

    # The spacing between grid points in each dimension.
    spacing = Tuple(Float, Float, Float)

    # A resampled/masked version of the data, suitable for rendering
    render_data = Property(Instance(tvtk.ImageData))
    _render_data = Instance(tvtk.ImageData)

    def _bounds_default(self):
        return tuple(np.array(self.spacing) * np.array(self.raw_data.shape))

    def _spacing_default(self):
        return (1.0, 1.0, 1.0)

    def _get_render_data(self):
        if self._render_data is None:
            self._render_data = self._prepare_data()
        return self._render_data

    def _get_mask_data(self):
        return self._mask_data

    def _set_mask_data(self, value):
        self._render_data = None
        self._mask_data = np.asfortranarray(value)

    def _get_raw_data(self):
        return self._raw_data

    def _set_raw_data(self, value):
        self._render_data = None
        self._raw_data = np.asfortranarray(value)

    def _prepare_data(self):
        image_data = _image_data_from_array(self.raw_data, self.spacing)
        resampled_data = _resample_data(image_data)

        if self.mask_data.size > 1:
            masked_data = _apply_mask(resampled_data, self.mask_data)
            return masked_data

        return resampled_data
