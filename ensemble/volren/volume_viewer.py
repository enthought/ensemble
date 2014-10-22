import numpy as np

from mayavi.core.ui.api import MlabSceneModel
from traits.api import Bool, CInt, HasTraits, Instance, List, on_trait_change
from tvtk.api import tvtk

from ensemble.ctf.api import CtfEditor, get_color
from .volume_data import VolumeData
from .volume_renderer import VolumeRenderer
from .volume_scene_member import ABCVolumeSceneMember

CLIP_MAX = 512


class VolumeViewer(HasTraits):
    # The view displayed
    model = Instance(MlabSceneModel, ())

    # The data to plot
    volume_data = Instance(VolumeData)

    # The volume renderer
    volume_renderer = Instance(VolumeRenderer)

    # Clip plane positions
    clip_bounds = List(CInt)

    # The transfer function editor
    ctf_editor = Instance(CtfEditor)

    # Whether to show the histogram on the CTF editor.
    histogram_bins = CInt(0)

    # If True, the Z-axis points down
    flip_z = Bool(False)

    # Additional members of the scene
    scene_members = List(Instance(ABCVolumeSceneMember))

    # -------------------------------------------------------------------------
    # Public interface
    # -------------------------------------------------------------------------

    def screenshot(self):
        """ Returns an image of the rendered volume. The image will be the same
        size as the window on screen.
        """
        render_window = self.model.render_window
        x, y = render_window.size

        data = tvtk.UnsignedCharArray()
        render_window.get_pixel_data(0, 0, x - 1, y - 1, 1, data)
        data_array = data.to_array().copy()
        data_array.shape = (y, x, 3)
        data_array = np.flipud(data_array)

        return data_array

    # -------------------------------------------------------------------------
    # Default values
    # -------------------------------------------------------------------------

    def _clip_bounds_default(self):
        return [0, CLIP_MAX, 0, CLIP_MAX, 0, CLIP_MAX]

    def _volume_renderer_default(self):
        function = self.ctf_editor.function
        return VolumeRenderer(data=self.volume_data,
                              colors=function.color,
                              opacities=function.opacity)

    def _ctf_editor_default(self):
        return CtfEditor(prompt_color_selection=get_color)

    # -------------------------------------------------------------------------
    # Traits notifications
    # -------------------------------------------------------------------------

    def _volume_data_changed(self):
        self.volume_renderer.data = self.volume_data

    def _clip_bounds_items_changed(self):
        self.volume_renderer.clip_bounds = self.clip_bounds[:]

    @on_trait_change('ctf_editor:function:updated')
    def ctf_updated(self):
        set_ctf = self.volume_renderer.set_transfer_function
        function = self.ctf_editor.function
        set_ctf(function.color, function.opacity)

    # -------------------------------------------------------------------------
    # Scene activation callbacks
    # -------------------------------------------------------------------------

    @on_trait_change('model.activated')
    def display_model(self):
        # Add the volume to the scene
        self.volume_renderer.add_volume_to_scene(self.model)

        # Add the other members to the scene
        volume_actor = self.volume_renderer.actor
        for member in self.scene_members:
            member.add_actors_to_scene(self.model, volume_actor)

        self._setup_camera()
        self.model.scene.background = (0, 0, 0)

        # Keep the view always pointing up
        interactor = self.model.scene.interactor
        interactor.interactor_style = tvtk.InteractorStyleTerrain()

    # -------------------------------------------------------------------------
    # Private methods
    # -------------------------------------------------------------------------

    def _setup_camera(self):
        if self.flip_z:
            view_up = (0, 0, -1)
            elevation = 100
        else:
            view_up = (0, 0, 1)
            elevation = 80
        self.model.mlab.view(40, elevation)
        self.model.camera.view_up = view_up

    @on_trait_change('histogram_bins,volume_data.raw_data')
    def _new_histogram(self):
        if (self.histogram_bins > 0 and
                self.volume_data is not None and
                self.volume_data.raw_data is not None):
            self.ctf_editor.histogram = np.histogram(self.volume_data.raw_data,
                                                     bins=self.histogram_bins,
                                                     density=False)
        else:
            self.ctf_editor.histogram = None
