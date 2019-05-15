from mayavi.sources.vtk_data_source import VTKDataSource
from mayavi.tools.tools import add_dataset
from traits.api import (HasStrictTraits, CInt, Enum, Instance, List, Property,
                        Range, on_trait_change)
from tvtk.api import tvtk

from ensemble.ctf.api import PiecewiseFunction
from .volume_3d import Volume3D, volume3d
from .volume_data import VolumeData

CLIP_MAX = 512
QUALITY_SETTINGS = {
    'best': {
        'mapper': {
            'sample_distance': 0.05,
        },
        'property': {
            'shade': False,
            'ambient': 0.5,
            'diffuse': 0.4,
            'specular': 0.1,
            'specular_power': 100,
        }
    },
    'default': {
        'mapper': {
            'sample_distance': 0.2,
        },
        'property': {
            'shade': False
        }
    },
    'performance': {
        'mapper': {
            'sample_distance': 1.0,
        },
        'property': {
            'shade': False
        }
    },
}


class VolumeRenderer(HasStrictTraits):
    # The data to plot
    data = Instance(VolumeData)

    # The mayavi data source for the volume data
    data_source = Instance(VTKDataSource)

    # The mayavi volume renderer object
    volume = Instance(Volume3D)

    # The tvtk.Actor for `volume`
    actor = Property(Instance(tvtk.Actor), depends_on='volume')

    # The minimum and maximum displayed intensity values.
    vmin = CInt(0)
    vmax = CInt(255)

    # The transfer function components
    opacities = Instance(PiecewiseFunction)
    colors = Instance(PiecewiseFunction)
    global_alpha = Range(0.0, 1.0, value=1.0)

    # Clip plane positions
    clip_bounds = List(CInt)

    # Render quality setting
    render_quality = Enum('default', QUALITY_SETTINGS.keys())

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    def add_volume_to_scene(self, scene_model):
        source = add_dataset(self.data.render_data,
                             figure=scene_model.mayavi_scene)
        self.data_source = source
        self.volume = volume3d(source, figure=scene_model.mayavi_scene)
        self._setup_volume()

    def set_transfer_function(self, colors=None, opacities=None):
        """ Update the volume mapper's transfer function.
        """
        lerp = lambda x: self.vmin + x * (self.vmax - self.vmin)  # noqa

        if colors is not None:
            self.colors = colors
        if opacities is not None:
            self.opacities = opacities

        color_tf = tvtk.ColorTransferFunction()
        for color in self.colors.values():
            color_tf.add_rgb_point(lerp(color[0]), *(color[1:]))

        opacity_tf = tvtk.PiecewiseFunction()
        alphas = self.opacities.values()
        for i, alpha in enumerate(alphas):
            x = alpha[0]
            if i > 0:
                # Look back one item. VTK doesn't like exact vertical jumps, so
                # we need to jog a value that is exactly equal by a little bit.
                if alphas[i-1][0] == alpha[0]:
                    x += 1e-8
            opacity_tf.add_point(lerp(x), alpha[1] * self.global_alpha)

        self._set_volume_ctf(color_tf, opacity_tf)

    # -------------------------------------------------------------------------
    # Traits bits
    # -------------------------------------------------------------------------

    def _clip_bounds_default(self):
        return [0, CLIP_MAX, 0, CLIP_MAX, 0, CLIP_MAX]

    @on_trait_change('data.raw_data')
    def _update_data(self):
        self.vmin = self.data.raw_data.min()
        self.vmax = self.data.raw_data.max()
        self._render_data_changed()

    @on_trait_change('data:mask_data')
    def _render_data_changed(self):
        if self.data_source is not None:
            image_data = self.data.render_data
            self.data_source.data = image_data
            self.data_source.update()
            self._setup_volume()

    def _clip_bounds_changed(self):
        self._set_volume_clip_planes()

    def _global_alpha_changed(self):
        self.set_transfer_function()

    def _render_quality_changed(self):
        self._setup_volume()

    def _get_actor(self):
        return self.volume.actors[0]

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def _setup_volume(self):
        render_settings = QUALITY_SETTINGS[self.render_quality]
        self.volume.volume_mapper.trait_set(**render_settings['mapper'])
        self.volume.volume_property.trait_set(**render_settings['property'])
        self._set_volume_clip_planes()
        self.set_transfer_function()

    def _set_volume_clip_planes(self):
        if self.data is None:
            return

        bounds = [b/CLIP_MAX for b in self.data.bounds]
        mn = [bounds[i]*pos for i, pos in enumerate(self.clip_bounds[::2])]
        mx = [bounds[i]*pos for i, pos in enumerate(self.clip_bounds[1::2])]
        planes = tvtk.Planes()
        # The planes need to be inside out to serve as clipping planes
        planes.set_bounds(mx[0], mn[0],
                          mx[1], mn[1],
                          mx[2], mn[2])
        # Set them as the clipping planes for the volume mapper
        self.volume.volume.mapper.clipping_planes = planes

    def _set_volume_ctf(self, color_tf, opacity_tf):
        if self.volume is not None:
            vp = self.volume.volume_property
            vp.set_scalar_opacity(opacity_tf)
            vp.set_color(color_tf)
            self.volume._update_ctf_fired()
