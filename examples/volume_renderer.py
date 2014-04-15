"""
Example of displaying a volume using the volume renderer.

This example creates a simple example volume with nested cylinders and a bit
of noise. The color bar on the bottom displays the transfer function that maps
values in the data to a color and opacity. Right click on the color bar to
alter the renderer's transfer function:

    * Add Color: Add a slider to control the color of intensity values.
    * Add Opacity: Adds a control point to adjust the shape of the
      transfer function, which controls the opacity of intensity values.

"""
import numpy as np

from enaml.qt.qt_application import QtApplication
import traits_enaml

from ensemble.volren.volume_data import VolumeData
from ensemble.volren.volume_renderer import VolumeRenderer

with traits_enaml.imports():
    from volume_renderer_window import VolumeRendererWindow


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


def show_volume(volume):
    app = QtApplication()
    volume_data = VolumeData(data=volume)
    renderer = VolumeRenderer(volume_data=volume_data)
    renderer.histogram_bins = 200
    win = VolumeRendererWindow(renderer=renderer)
    win.show()
    app.start()


def main():
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-n', '--node', default='/ct',
                        help='The path to the node in the HDF5 file '
                             'containing the volume data.')
    parser.add_argument('volume_file', nargs='?',
                        help='The HDF5 file containing the volume data. '
                             'If omitted, an example volume will be '
                             'generated.')

    args = parser.parse_args()
    if args.volume_file is None:
        h5 = None
        volume = example_volume()
    else:
        import tables
        h5 = tables.openFile(args.volume_file)
        volume = h5.getNode(args.node)[:].T
    show_volume(volume)
    if h5 is not None:
        h5.close()


if __name__ == '__main__':
    main()
