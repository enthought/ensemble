from __future__ import unicode_literals
from mayavi.core.trait_defs import DEnum
from mayavi.modules.volume import Volume
from mayavi.tools.modules import DataModuleFactory, make_function
from traits.api import Instance, Unicode


class Volume3D(Volume):
    """ Subclass to provide access to VolumeTextureMapper3D.
    """

    volume_mapper_type = DEnum(values_name='_mapper_types',
                               value='VolumeTextureMapper3D',
                               desc='volume mapper to use')

    def _update_ctf_fired(self):
        self.render()


class Volume3DFactory(DataModuleFactory):
    """ Applies the Volume3D Mayavi module to the given VTK data source.
    """
    _target = Instance(Volume3D, ())
    volume_mapper_type = Unicode('SmartVolumeMapper',
                                 adapts='volume_mapper_type')


volume3d = make_function(Volume3DFactory)
