"""
Example of displaying a volume using the volume viewer.

This example creates a simple example volume with nested cylinders and a bit
of noise. The color bar on the bottom displays the transfer function that maps
values in the data to a color and opacity. Right click on the color bar to
alter the viewer's transfer function:

    * Add Color: Add a slider to control the color of intensity values.
    * Add Opacity: Adds a control point to adjust the shape of the
      transfer function, which controls the opacity of intensity values.

"""
import argparse
from contextlib import closing

import numpy as np

from enaml.qt.qt_application import QtApplication
import traits_enaml

from ensemble.volren.volume_bounding_box import VolumeBoundingBox
from ensemble.volren.volume_data import VolumeData
from ensemble.volren.volume_viewer import VolumeViewer

with traits_enaml.imports():
    from volume_viewer_window import VolumeViewerWindow


def build_volume_data(cmdline_args):
    if cmdline_args.volume_file is None:
        volume = example_volume()
    else:
        import tables

        with closing(tables.openFile(cmdline_args.volume_file)) as h5:
            volume = h5.getNode(cmdline_args.node)[:].T

    volume_data_kwargs = {'raw_data': volume}
    if cmdline_args.mask:
        volume_data_kwargs['mask_data'] = example_volume_mask(volume)

    return VolumeData(**volume_data_kwargs)


def example_volume_mask(volume_array):
    mask = np.zeros_like(volume_array)
    depth, height, width = mask.shape
    half = (depth/2, height/2, width/2)
    quarter = (depth/4, height/4, width/4)
    axis_slices = [slice(half[i]-quarter[i], half[i]+quarter[i])
                   for i in range(3)]
    mask[axis_slices[0], axis_slices[1], axis_slices[2]] = 255
    return mask


def example_volume(size=61, height=80):
    cross_section = example_cross_section(size)
    volume = np.tile(cross_section, (height, 1, 1))
    volume = volume + 0.2 * np.random.normal(size=volume.shape)
    return rescale_uint8(volume)


def example_cross_section(size):
    # Create a grid with x/y distances from the center point.
    r = size // 2
    grid = slice(-r, r, size * 1j)
    x, y = np.mgrid[grid, grid]

    # Create circle of ones, with a smaller circle of twos inside.
    disks = np.zeros((size, size))
    radial_dist = np.sqrt(x**2 + y**2)
    disks[radial_dist < r] = 1
    disks[radial_dist < r/2] = 2
    return disks


def rescale_uint8(array):
    array = 255 * (array - array.min()) / array.ptp()
    return array.astype(np.uint8)


def show_volume(volume_data):
    app = QtApplication()
    scene_members = [VolumeBoundingBox()]
    viewer = VolumeViewer(volume_data=volume_data, histogram_bins=256,
                          scene_members=scene_members)
    win = VolumeViewerWindow(viewer=viewer)
    win.show()
    app.start()


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m', '--mask', action='store_true',
                        help='Whether or not the data should be masked.')
    parser.add_argument('-n', '--node', default='/ct',
                        help='The path to the node in the HDF5 file '
                             'containing the volume data.')
    parser.add_argument('volume_file', nargs='?',
                        help='The HDF5 file containing the volume data. '
                             'If omitted, an example volume will be '
                             'generated.')

    args = parser.parse_args()
    volume_data = build_volume_data(args)
    show_volume(volume_data)


if __name__ == '__main__':
    main()
