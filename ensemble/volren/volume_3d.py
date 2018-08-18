import vtk
from vtk.util import vtkConstants

from mayavi.core.common import error
from mayavi.core.trait_defs import DEnum
from mayavi.modules.volume import Volume
from mayavi.tools.modules import DataModuleFactory, make_function
from traits.api import Dict, Instance, Str
from tvtk.api import tvtk
from tvtk.common import configure_input


class Volume3D(Volume):
    """ Subclass to provide access to VolumeTextureMapper3D.
    """

    volume_mapper_type = DEnum(values_name='_mapper_types',
                               value='VolumeTextureMapper3D',
                               desc='volume mapper to use')

    def _update_ctf_fired(self):
        self.render()

    def _setup_mapper_types(self):
        """Sets up the mapper based on input data types.
        """
        input = self.module_manager.source.get_output_dataset()
        data_types = (vtkConstants.VTK_UNSIGNED_CHAR,
                      vtkConstants.VTK_UNSIGNED_SHORT)
        mapper_types = []
        if input.point_data.scalars.data_type not in data_types:
            if 'FixedPointVolumeRayCastMapper' in self._available_mapper_types:
                mapper_types = ['FixedPointVolumeRayCastMapper']
            else:
                error('Available volume mappers only work with \
                      unsigned_char or unsigned_short datatypes')
        else:
            mapper_types = ['TextureMapper2D', 'RayCastMapper']
            check = ['FixedPointVolumeRayCastMapper', 'VolumeProMapper']
            for mapper in check:
                if mapper in self._available_mapper_types:
                    mapper_types.append(mapper)
        mapper_types.append('VolumeTextureMapper3D')
        self._mapper_types = mapper_types

    def _volume_mapper_type_changed(self, value):
        if self.module_manager is None:
            return

        old_vm = self._volume_mapper
        if old_vm is not None:
            old_vm.on_trait_change(self.render, remove=True)

        ray_cast_functions = ['']
        if value == 'RayCastMapper':
            new_vm = self._get_mapper(tvtk.VolumeRayCastMapper)
            vrc_func = tvtk.VolumeRayCastCompositeFunction()
            new_vm.volume_ray_cast_function = vrc_func
            ray_cast_functions = ['RayCastCompositeFunction',
                                  'RayCastMIPFunction',
                                  'RayCastIsosurfaceFunction']
        elif value == 'TextureMapper2D':
            new_vm = self._get_mapper(tvtk.VolumeTextureMapper2D)
        elif value == 'VolumeTextureMapper3D':
            new_vm = self._get_mapper(tvtk.VolumeTextureMapper3D)
        elif value == 'VolumeProMapper':
            new_vm = self._get_mapper(tvtk.VolumeProMapper)
        elif value == 'FixedPointVolumeRayCastMapper':
            new_vm = self._get_mapper(tvtk.FixedPointVolumeRayCastMapper)
        else:
            msg = "Unsupported volume mapper type: '{0}'".format(value)
            raise ValueError(msg)

        self._volume_mapper = new_vm
        self._ray_cast_functions = ray_cast_functions

        configure_input(new_vm, self.module_manager.source.outputs[0])
        self.volume.mapper = new_vm
        new_vm.on_trait_change(self.render)

    # Cache of mappers keyed by class
    _mappers = Dict

    def _get_mapper(self, klass):
        """ Return a mapper of the given class. Either from the cache or by
        making a new one.
        """
        result = self._mappers.get(klass)
        if result is None:
            result = klass()
            self._mappers[klass] = result
        return result


class Volume3DFactory(DataModuleFactory):
    """ Applies the Volume3D Mayavi module to the given VTK data source.
    """
    _target = Instance(Volume3D, ())
    volume_mapper_type = Str('VolumeTextureMapper3D',
                             adapts='volume_mapper_type')


class SmartVolume3D(Volume3D):
    """ Subclass to provide access to SmartVolumeMapper
    """
    def _volume_mapper_type_changed(self, value):
        if self.module_manager is None:
            return

        old_vm = self._volume_mapper
        if old_vm is not None:
            old_vm.on_trait_change(self.render, remove=True)

        new_vm = self._get_mapper(tvtk.SmartVolumeMapper)
        new_vm.requested_render_mode = 'default'

        self._volume_mapper = new_vm

        configure_input(new_vm, self.module_manager.source.outputs[0])
        self.volume.mapper = new_vm
        new_vm.on_trait_change(self.render)


class SmartVolume3DFactory(DataModuleFactory):
    """ Applies the Volume3D Mayavi module to the given VTK data source.
    """
    _target = Instance(SmartVolume3D, ())


vtk_major_version = vtk.vtkVersion().GetVTKMajorVersion()


if vtk_major_version > 6:
    volume3d = make_function(SmartVolume3DFactory)
else:
    volume3d = make_function(Volume3DFactory)
