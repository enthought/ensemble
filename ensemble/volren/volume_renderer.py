from mayavi.core.ui.api import MlabSceneModel
from mayavi.tools.tools import add_dataset
from traits.api import HasTraits, CInt, Float, Instance, List, on_trait_change
from tvtk.api import tvtk

from ensemble.ctf.editor import CtfEditor
from ensemble.ctf.gui_utils import get_color, get_filename
from ensemble.volren.volume_3d import Volume3D, volume3d
from ensemble.volren.volume_data import VolumeData

CLIP_MAX = 100


class VolumeRenderer(HasTraits):
    # The view displayed
    model = Instance(MlabSceneModel, ())

    # The data to plot
    volume_data = Instance(VolumeData)

    # The volume object
    volume = Instance(Volume3D)

    # The minimum and maximum displayed intensity values.
    vmin = CInt(0)
    vmax = CInt(255)

    # Clip plane positions
    clip_bounds = List(Float)

    # The transfer function editor
    ctf_editor = Instance(CtfEditor)

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

    def _clip_bounds_items_changed(self):
        self._set_volume_clip_planes()

    @on_trait_change('ctf_editor.function_updated')
    def ctf_updated(self):
        ctf = tvtk.ColorTransferFunction()
        otf = tvtk.PiecewiseFunction()
        lerp = lambda x: self.vmin + x * (self.vmax - self.vmin)

        for color in self.ctf_editor.colors.items():
            ctf.add_rgb_point(lerp(color[0]), *(color[1:]))
        for alpha in self.ctf_editor.opacities.items():
            otf.add_point(lerp(alpha[0]), alpha[1])

        self._set_volume_ctf(ctf, otf)

    #--------------------------------------------------------------------------
    # Scene activation callbacks
    #--------------------------------------------------------------------------

    @on_trait_change('model.activated')
    def display_model(self):
        sf = add_dataset(self.volume_data.resampled_image_data,
                         figure=self.model.mayavi_scene)
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
        self.volume.volume_mapper.trait_set(sample_distance=0.2)
        self.volume.volume_property.trait_set(shade=False)
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
        vp = self.volume.volume_property
        vp.set_scalar_opacity(otf)
        vp.set_color(ctf)
        self.volume._update_ctf_fired()
