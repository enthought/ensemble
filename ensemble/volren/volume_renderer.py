import numpy as np

from mayavi.core.ui.api import MlabSceneModel
from mayavi.sources.vtk_data_source import VTKDataSource
from mayavi.tools.tools import add_dataset
from traits.api import (Bool, CInt, Float, HasTraits, Instance, List, Tuple,
                        on_trait_change)
from tvtk.api import tvtk

from ensemble.ctf.editor import CtfEditor
from ensemble.ctf.gui_utils import get_color, get_filename
from ensemble.volren.volume_3d import Volume3D, volume3d
from ensemble.volren.volume_data import VolumeData

CLIP_MAX = 512

FloatPair = Tuple(Float, Float)


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
    clip_bounds = List(CInt)

    # The transfer function editor
    ctf_editor = Instance(CtfEditor)

    # Whether to show the histogram on the CTF editor.
    histogram_bins = CInt(0)

    # If True, the Z-axis points down
    flip_z = Bool(False)

    # If True, draw an outline of the volume's bounding box
    show_outline = Bool(True)

    # What are the physical value ranges for each axis?
    visible_axis_ranges = Tuple(FloatPair, FloatPair, FloatPair)

    # Which axes should have a scale shown?
    visible_axis_scales = Tuple(Bool, Bool, Bool)

    #--------------------------------------------------------------------------
    # Default values
    #--------------------------------------------------------------------------

    def _clip_bounds_default(self):
        return [0, CLIP_MAX, 0, CLIP_MAX, 0, CLIP_MAX]

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
        self.vmin = self.volume_data.data.min()
        self.vmax = self.volume_data.data.max()

        if self.volume_data_source is not None:
            image_data = self.volume_data.resampled_image_data
            self.volume_data_source.data = image_data
            self.volume_data_source.update()
            self._setup_volume()

    def _clip_bounds_items_changed(self):
        self._set_volume_clip_planes()

    @on_trait_change('ctf_editor.function_updated')
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
            otf.add_point(lerp(x), alpha[1])

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

        if self.flip_z:
            view_up = (0, 0, -1)
            elevation = 100
        else:
            view_up = (0, 0, 1)
            elevation = 80
        self.model.mlab.view(40, elevation)
        self.model.camera.view_up = view_up
        self.model.scene.background = (0, 0, 0)

        # Keep the view always pointing up
        interactor = self.model.scene.interactor
        interactor.interactor_style = tvtk.InteractorStyleTerrain()

        # Add some addition actors to the scene
        self._add_axis_actors()

    #--------------------------------------------------------------------------
    # Private methods
    #--------------------------------------------------------------------------

    def _add_axis_actors(self):
        # Some axes with ticks
        if any(self.visible_axis_scales):
            bounds = self.volume.actors[0].bounds
            x_vis, y_vis, z_vis = self.visible_axis_scales
            x_range, y_range, z_range = self.visible_axis_ranges
            cube_axes = tvtk.CubeAxesActor(
                bounds=bounds,
                camera=self.model.camera,
                tick_location='outside',
                x_title='', x_units='',
                y_title='', y_units='',
                z_title='', z_units='',
                x_axis_visibility=x_vis,
                y_axis_visibility=y_vis,
                z_axis_visibility=z_vis,
                x_axis_range=x_range,
                y_axis_range=y_range,
                z_axis_range=z_range,
            )
            self.model.renderer.add_actor(cube_axes)

        # An outline of the bounds of the data
        if self.show_outline:
            outline = tvtk.OutlineFilter(
                input=self.volume_data.resampled_image_data
            )
            outline_mapper = tvtk.PolyDataMapper(
                input=outline.output
            )
            outline_actor = tvtk.Actor(mapper=outline_mapper)
            self.model.renderer.add_actor(outline_actor)

    def _setup_volume(self):
        self.volume.volume_mapper.trait_set(sample_distance=0.2)
        self.volume.volume_property.trait_set(shade=False)
        self._set_volume_clip_planes()
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
