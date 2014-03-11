import argparse
from contextlib import closing

import numpy as np
import tables

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

from enaml.qt.qt_application import QtApplication
import traits_enaml

from ensemble.volren.volume_data import VolumeData
from ensemble.volren.volume_renderer import VolumeRenderer

with traits_enaml.imports():
    from volume_renderer_window import VolumeRendererWindow


def show_volume(volume_file, node_path, slice_range, spacing, flip):
    with closing(tables.openFile(volume_file, mode='r')) as h5:
        volume = h5.getNode(node_path)[:]
    volume = np.swapaxes(volume, 0, -1)

    data_spacing = tuple(spacing[1:]) + (spacing[0],)
    if flip:
        volume = volume[:, :, ::-1]

    app = QtApplication()
    volume_data = VolumeData(data=volume, spacing=data_spacing)
    renderer = VolumeRenderer(volume_data=volume_data)
    win = VolumeRendererWindow(renderer=renderer)
    win.show()
    app.start()


def main():
    formatter = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument('volume_file', help="HDF5 file containing CT 3D data.")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Set logging verbosity to 'debug'.")
    parser.add_argument('-r', '--range', nargs=2, type=int,
                        help="Slice range to display.")
    parser.add_argument('-s', '--spacing', nargs=3, default=(1.0, 1.0, 1.0),
                        type=float, help="Spacing for the data array.")
    parser.add_argument('-n', '--node', default='/ct',
                        help="Node name for CT volume in the HDF5 file.")
    parser.add_argument('-f', '--flip', action='store_true',
                        help="Flip z-direction of the volume.")

    args = parser.parse_args()

    show_volume(args.volume_file, args.node, args.range, args.spacing,
                args.flip)


if __name__ == '__main__':
    main()
