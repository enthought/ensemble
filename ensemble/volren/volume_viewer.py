import numpy as np

from mayavi.core.ui.api import MlabSceneModel
from traits.api import (Bool, CInt, Float, HasTraits, Instance, List, Tuple,
                        on_trait_change)
from tvtk.api import tvtk

from ensemble.ctf.editor import CtfEditor
from ensemble.ctf.gui_utils import get_color, get_filename
from .volume_data import VolumeData
from .volume_renderer import VolumeRenderer

CLIP_MAX = 512

FloatPair = Tuple(Float, Float)


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

    # If True, draw an outline of the volume's bounding box
    show_outline = Bool(True)

    # If True, show the minor tick marks on the CubeAxesActor
    show_axis_minor_ticks = Bool(False)

    # What are the physical value ranges for each axis?
    visible_axis_ranges = Tuple(FloatPair, FloatPair, FloatPair)

    # Which axes should have a scale shown?
    visible_axis_scales = Tuple(Bool, Bool, Bool)

    #--------------------------------------------------------------------------
    # Public interface
    #--------------------------------------------------------------------------

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

    #--------------------------------------------------------------------------
    # Default values
    #--------------------------------------------------------------------------

    def _clip_bounds_default(self):
        return [0, CLIP_MAX, 0, CLIP_MAX, 0, CLIP_MAX]

    def _volume_renderer_default(self):
        return VolumeRenderer(data=self.volume_data,
                              colors=self.ctf_editor.colors,
                              opacities=self.ctf_editor.opacities,
                              show_outline=self.show_outline,
                              show_axis_minor_ticks=self.show_axis_minor_ticks,
                              visible_axis_ranges=self.visible_axis_ranges,
                              visible_axis_scales=self.visible_axis_scales)

    def _ctf_editor_default(self):
        return CtfEditor(prompt_color_selection=get_color,
                         prompt_file_selection=get_filename)

    def _visible_axis_ranges_default(self):
        return ((0.0, 1.0), (0.0, 1.0), (0.0, 1.0))

    def _visible_axis_scales_default(self):
        return (False, False, False)

    #--------------------------------------------------------------------------
    # Traits notifications
    #--------------------------------------------------------------------------

    def _volume_data_changed(self):
        self.volume_renderer.data = self.volume_data

    def _clip_bounds_items_changed(self):
        self.volume_renderer.clip_bounds = self.clip_bounds[:]

    @on_trait_change('ctf_editor.function_updated')
    def ctf_updated(self):
        set_ctf = self.volume_renderer.set_transfer_function
        set_ctf(self.ctf_editor.colors, self.ctf_editor.opacities)

    #--------------------------------------------------------------------------
    # Scene activation callbacks
    #--------------------------------------------------------------------------

    @on_trait_change('model.activated')
    def display_model(self):
        # Add the volume to the scene
        self.volume_renderer.initialize_actors(self.model)

        self._setup_camera()
        self.model.scene.background = (0, 0, 0)

        # Keep the view always pointing up
        interactor = self.model.scene.interactor
        interactor.interactor_style = tvtk.InteractorStyleTerrain()

    #--------------------------------------------------------------------------
    # Private methods
    #--------------------------------------------------------------------------

    def _setup_camera(self):
        if self.flip_z:
            view_up = (0, 0, -1)
            elevation = 100
        else:
            view_up = (0, 0, 1)
            elevation = 80
        self.model.mlab.view(40, elevation)
        self.model.camera.view_up = view_up

    @on_trait_change('histogram_bins,volume_data')
    def _new_histogram(self):
        if (self.histogram_bins > 0 and
                self.volume_data is not None and
                self.volume_data.raw_data is not None):
            self.ctf_editor.histogram = np.histogram(self.volume_data.raw_data,
                                                     bins=self.histogram_bins,
                                                     density=False)
        else:
            self.ctf_editor.histogram = None
