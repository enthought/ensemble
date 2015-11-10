from traits.api import Bool, Enum, Float, Str, Tuple
from tvtk.api import tvtk

from .volume_scene_member import ABCVolumeSceneMember

# Convenience for the trait definitions below
FloatPair = Tuple(Float, Float)


class VolumeAxes(ABCVolumeSceneMember):
    """ An object which builds a CubeAxesActor for a scene containing a Volume.
    """

    # If True, show the minor tick marks on the CubeAxesActor
    show_axis_minor_ticks = Bool(False)

    # What are the physical value ranges for each axis?
    visible_axis_ranges = Tuple(FloatPair, FloatPair, FloatPair)

    # Which axes should have a scale shown?
    visible_axis_scales = Tuple(Bool, Bool, Bool)

    # Axes titles.
    axis_titles = Tuple(Str, Str, Str)

    # Axes units.
    axis_units = Tuple(Str, Str, Str)

    # Fly mode, determining the position of the axes on the bounding box.
    fly_mode = Enum(('static_triad', 'closest_triad', 'furthest_triad',
                     'outer_edges', 'static_edges'))

    #--------------------------------------------------------------------------
    # ABCVolumeSceneMember interface
    #--------------------------------------------------------------------------

    def add_actors_to_scene(self, scene_model, volume_actor):

        # Some axes with ticks
        if any(self.visible_axis_scales):
            bounds = volume_actor.bounds
            x_vis, y_vis, z_vis = self.visible_axis_scales
            x_range, y_range, z_range = self.visible_axis_ranges
            x_title, y_title, z_title = self.axis_titles
            x_units, y_units, z_units = self.axis_units
            cube_axes = tvtk.CubeAxesActor(
                bounds=bounds,
                camera=scene_model.camera,
                tick_location='outside',
                x_title=x_title, x_units=x_units,
                y_title=y_title, y_units=y_units,
                z_title=z_title, z_units=z_units,
                x_axis_visibility=x_vis,
                y_axis_visibility=y_vis,
                z_axis_visibility=z_vis,
                x_axis_range=x_range,
                y_axis_range=y_range,
                z_axis_range=z_range,
                x_axis_minor_tick_visibility=self.show_axis_minor_ticks,
                y_axis_minor_tick_visibility=self.show_axis_minor_ticks,
                z_axis_minor_tick_visibility=self.show_axis_minor_ticks,
                fly_mode=self.fly_mode,
            )
            scene_model.renderer.add_actor(cube_axes)

    #--------------------------------------------------------------------------
    # Default values
    #--------------------------------------------------------------------------

    def _visible_axis_ranges_default(self):
        return ((0.0, 1.0), (0.0, 1.0), (0.0, 1.0))

    def _visible_axis_scales_default(self):
        return (False, False, False)
