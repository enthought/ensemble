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
import numpy as np

from enaml.qt.qt_application import QtApplication
import traits_enaml

from ensemble.volren.volume_bounding_box import VolumeBoundingBox
from ensemble.volren.volume_data import VolumeData
from ensemble.volren.volume_viewer import VolumeViewer

with traits_enaml.imports():
    from volume_viewer_window import VolumeViewerWindow


def main():
    volume = example_volume()
    show_volume(volume)


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
    volume_data = VolumeData(raw_data=volume)
    scene_members = [VolumeBoundingBox()]
    viewer = VolumeViewer(volume_data=volume_data, histogram_bins=256,
                          scene_members=scene_members)
    win = VolumeViewerWindow(viewer=viewer)
    win.show()
    app.start()


if __name__ == '__main__':
    main()
