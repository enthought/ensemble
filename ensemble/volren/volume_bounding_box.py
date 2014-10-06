from tvtk.api import tvtk

from .volume_scene_member import ABCVolumeSceneMember


class VolumeBoundingBox(ABCVolumeSceneMember):
    """ An object which builds an bounding box actor for a scene containing a
    Volume.
    """

    #--------------------------------------------------------------------------
    # ABCVolumeSceneMember interface
    #--------------------------------------------------------------------------

    def add_actors_to_scene(self, scene_model, volume_actor):

        # An outline of the bounds of the Volume actor's data
        outline = tvtk.OutlineFilter(input=volume_actor.mapper.input)
        outline_mapper = tvtk.PolyDataMapper(input=outline.output)
        outline_actor = tvtk.Actor(mapper=outline_mapper)
        outline_actor.property.opacity = 0.3
        scene_model.renderer.add_actor(outline_actor)
