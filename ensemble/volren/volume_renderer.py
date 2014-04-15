import numpy as np

from mayavi.core.ui.api import MlabSceneModel
from mayavi.sources.vtk_data_source import VTKDataSource
from mayavi.tools.tools import add_dataset
from traits.api import CInt, Enum, Float, HasTraits, Instance, List, \
    Range, on_trait_change
from tvtk.api import tvtk

from ensemble.ctf.editor import CtfEditor
from ensemble.ctf.gui_utils import get_color, get_filename
from ensemble.volren.volume_3d import Volume3D, volume3d
from ensemble.volren.volume_data import VolumeData

CLIP_MAX = 100
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


class VolumeRenderer(HasTraits):
    # The view displayed
    model = Instance(MlabSceneModel, ())

    # The data to plot
    volume_data = Instance(VolumeData)

    # The mayavi data source for the volume data
    volume_data_source = Instance(VTKDataSource)

    # The mayavi volume renderer object
    volume = Instance(Volume3D)

    # The minimum and maximum displayed intensity values.
    vmin = CInt(0)
    vmax = CInt(255)

    # Clip plane positions
    clip_bounds = List(Float)

    # Render quality setting
    render_quality = Enum('performance', QUALITY_SETTINGS.keys())

    # The transfer function editor
    ctf_editor = Instance(CtfEditor)

    # Whether to show the histogram on the CTF editor.
    histogram_bins = CInt(0)

    # A global multiplier to the opacity transfer function.
    global_alpha = Range(0.0, 1.0, value=1.0)

    #--------------------------------------------------------------------------
    # Default values
    #--------------------------------------------------------------------------

    def _clip_bounds_default(self):
        return [0, CLIP_MAX, 0, CLIP_MAX, 0, CLIP_MAX]

    def _ctf_editor_default(self):
        return CtfEditor(prompt_color_selection=get_color,
                         prompt_file_selection=get_filename)

    #--------------------------------------------------------------------------
    # Traits notifications
    #--------------------------------------------------------------------------

    def _volume_data_changed(self):
        self.vmin = self.volume_data.data.min()
        self.vmax = self.volume_data.data.max()

        if self.volume_data_source is not None:
            image_data = self.volume_data.resampled_image_data
            self.volume_data_source.data = image_data
            self.volume_data_source.update()
            self._setup_volume()

    def _clip_bounds_items_changed(self):
        self._set_volume_clip_planes()

    def _render_quality_changed(self):
        self._setup_volume()

    @on_trait_change('ctf_editor.function_updated,global_alpha')
    def ctf_updated(self):
        ctf = tvtk.ColorTransferFunction()
        otf = tvtk.PiecewiseFunction()
        lerp = lambda x: self.vmin + x * (self.vmax - self.vmin)

        for color in self.ctf_editor.colors.items():
            ctf.add_rgb_point(lerp(color[0]), *(color[1:]))
        alphas = self.ctf_editor.opacities.items()
        for i, alpha in enumerate(alphas):
            x = alpha[0]
            if i > 0:
                # Look back one item. VTK doesn't like exact vertical jumps, so
                # we need to jog a value that is exactly equal by a little bit.
                if alphas[i-1][0] == alpha[0]:
                    x += 1e-8
            otf.add_point(lerp(x), alpha[1] * self.global_alpha)

        self._set_volume_ctf(ctf, otf)

    #--------------------------------------------------------------------------
    # Scene activation callbacks
    #--------------------------------------------------------------------------

    @on_trait_change('model.activated')
    def display_model(self):
        sf = add_dataset(self.volume_data.resampled_image_data,
                         figure=self.model.mayavi_scene)
        self.volume_data_source = sf
        self.volume = volume3d(sf, figure=self.model.mayavi_scene)
        self._setup_volume()

        self.model.mlab.view(40, 50)
        self.model.scene.background = (0, 0, 0)

        # Keep the view always pointing up
        interactor = self.model.scene.interactor
        interactor.interactor_style = tvtk.InteractorStyleTerrain()

    #--------------------------------------------------------------------------
    # Private methods
    #--------------------------------------------------------------------------

    def _setup_volume(self):
        render_settings = QUALITY_SETTINGS[self.render_quality]
        self.volume.volume_mapper.trait_set(**render_settings['mapper'])
        self.volume.volume_property.trait_set(**render_settings['property'])
        self.ctf_updated()

    def _set_volume_clip_planes(self):
        bounds = [b/CLIP_MAX for b in self.volume_data.bounds]
        mn = [bounds[i]*pos for i, pos in enumerate(self.clip_bounds[::2])]
        mx = [bounds[i]*pos for i, pos in enumerate(self.clip_bounds[1::2])]
        planes = tvtk.Planes()
        # The planes need to be inside out to serve as clipping planes
        planes.set_bounds(mx[0], mn[0],
                          mx[1], mn[1],
                          mx[2], mn[2])
        # Set them as the clipping planes for the volume mapper
        self.volume.volume.mapper.clipping_planes = planes

    def _set_volume_ctf(self, ctf, otf):
        if self.volume is not None:
            vp = self.volume.volume_property
            vp.set_scalar_opacity(otf)
            vp.set_color(ctf)
            self.volume._update_ctf_fired()

    @on_trait_change('histogram_bins,volume_data')
    def _new_histogram(self):
        if (self.histogram_bins > 0 and
                self.volume_data is not None and
                self.volume_data.data is not None):
            self.ctf_editor.histogram = np.histogram(self.volume_data.data,
                                                     bins=self.histogram_bins,
                                                     density=False)
        else:
            self.ctf_editor.histogram = None
