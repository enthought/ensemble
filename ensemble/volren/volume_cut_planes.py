from collections import OrderedDict

from mayavi import mlab
from mayavi.core.api import PipelineBase
from traits.api import Enum, Instance, List, Range, Str, on_trait_change

from .volume_scene_member import ABCVolumeSceneMember


CUT_COLORMAPS = OrderedDict([
    (u'Gray', 'gray'),
    (u'Bone', 'bone'),
    (u'RdBu', 'RdBu'),
])


class VolumeCutPlanes(ABCVolumeSceneMember):
    """ An object which adds image cut planes to a scene containing a Volume.
    """

    # Image slices.
    image_plane_widget_x = Instance(PipelineBase)
    image_plane_widget_y = Instance(PipelineBase)
    image_plane_widget_z = Instance(PipelineBase)

    # Colormap selection
    available_cut_colormaps = List(Str, CUT_COLORMAPS.keys())
    selected_cut_color_map = Enum(values='available_cut_colormaps')

    # A global multiplier to the opacity transfer function.
    slicer_alpha = Range(0.0, 1.0, value=1.0)

    # Image planes brightness and contrast
    cut_brightness = Range(-1.0, 1.0, value=0.0)
    cut_contrast = Range(-1.0, 1.0, value=0.0)

    # -------------------------------------------------------------------------
    # ABCVolumeSceneMember interface
    # -------------------------------------------------------------------------

    def add_actors_to_scene(self, scene_model, volume_actor):
        data_source = self._find_volume_data_source(scene_model, volume_actor)
        if data_source is None:
            return

        for axis in 'xyz':
            ipw = mlab.pipeline.image_plane_widget(
                data_source, figure=scene_model.mayavi_scene,
                plane_orientation=axis + '_axes',
            )
            lut_manager = ipw.module_manager.scalar_lut_manager
            lut_manager.lut_mode = CUT_COLORMAPS[self.selected_cut_color_map]
            ipw.ipw.texture_plane_property.opacity = self.slicer_alpha
            ipw.visible = False
            setattr(self, 'image_plane_widget_' + axis, ipw)

    # -------------------------------------------------------------------------
    # Traits notifications
    # -------------------------------------------------------------------------

    def _slicer_alpha_changed(self, alpha):
        for ipw in self._iter_image_plane_widgets():
            ipw.ipw.texture_plane_property.opacity = alpha
            ipw.render()

    def _selected_cut_color_map_changed(self, new):
        for ipw in self._iter_image_plane_widgets():
            lut_manager = ipw.module_manager.scalar_lut_manager
            lut_manager.lut_mode = CUT_COLORMAPS[new]
            ipw.render()

    @on_trait_change('cut_brightness,cut_contrast,image_plane_widget_z')
    def _on_cut_brightness_contrast(self):
        if self.image_plane_widget_z is not None:
            # This is shared between all three.
            plane_widget = self.image_plane_widget_z
            lut_manager = plane_widget.module_manager.scalar_lut_manager

            lut_manager.use_default_range = False
            data_low, data_high = lut_manager.default_data_range
            data_level = (data_low + data_high) / 2.0
            data_radius = (data_high - data_low) / 2.0
            level = data_level - data_radius * self.cut_brightness
            radius = data_radius * pow(2, -self.cut_contrast)
            lut_manager.data_range = (level - radius, level + radius)

            for ipw in self._iter_image_plane_widgets():
                ipw.render()

    # -------------------------------------------------------------------------
    # Private interface
    # -------------------------------------------------------------------------

    def _find_volume_data_source(self, scene_model, volume_actor):
        volume_image_data = volume_actor.mapper.input
        for child in scene_model.mayavi_scene.children:
            if volume_image_data == child.get_output_dataset():
                return child

        return None

    def _iter_image_plane_widgets(self):
        image_plane_widgets = (
            self.image_plane_widget_x, self.image_plane_widget_y,
            self.image_plane_widget_z
        )
        for ipw in image_plane_widgets:
            if ipw is not None:
                yield ipw
