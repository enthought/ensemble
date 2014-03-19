import numpy as np

from enaml.qt.qt_application import QtApplication
import traits_enaml

from ensemble.volren.volume_data import VolumeData
from ensemble.volren.volume_renderer import VolumeRenderer

with traits_enaml.imports():
    from volume_renderer_window import VolumeRendererWindow


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
    volume_data = VolumeData(data=volume, spacing=(1, 1, 1))
    renderer = VolumeRenderer(volume_data=volume_data)
    win = VolumeRendererWindow(renderer=renderer)
    win.show()
    app.start()


if __name__ == '__main__':
    main()
