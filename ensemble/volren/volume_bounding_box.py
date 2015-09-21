from traits.api import Int
from tvtk.api import tvtk
from tvtk.common import configure_input_data

from .volume_scene_member import ABCVolumeSceneMember


class VolumeBoundingBox(ABCVolumeSceneMember):
    """ An object which builds an bounding box actor for a scene containing a
    Volume.
    """

    # The number of points should be 8 after the bounding box is computed
    number_of_points = Int(0)

    #--------------------------------------------------------------------------
    # ABCVolumeSceneMember interface
    #--------------------------------------------------------------------------

    def add_actors_to_scene(self, scene_model, volume_actor):

        # An outline of the bounds of the Volume actor's data
        outline = tvtk.OutlineFilter()
        configure_input_data(outline, volume_actor.mapper.input)
        outline.update()
        self.number_of_points = outline.output.number_of_points
        outline_mapper = tvtk.PolyDataMapper()
        configure_input_data(outline_mapper, outline.output)
        outline_actor = tvtk.Actor(mapper=outline_mapper)
        outline_actor.property.opacity = 0.3
        scene_model.renderer.add_actor(outline_actor)
