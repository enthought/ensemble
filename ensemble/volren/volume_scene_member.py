from abc import abstractmethod

from traits.api import ABCHasStrictTraits


class ABCVolumeSceneMember(ABCHasStrictTraits):
    """ An abstract base class for object which contribute actors to a mayavi
    scene which contains a `Volume` actor.
    """

    @abstractmethod
    def add_actors_to_scene(self, scene_model):
        """ Add actors to the mayavi scene `scene_model`.
        """

    @staticmethod
    def find_volume_actor(scene_model):
        """ Return the first `Volume` actor found in a Mayavi `SceneModel`.
        """
        import tvtk  # An expensive import that should be deferred

        volume_class = tvtk.tvtk_classes.volume.Volume

        for actor in scene_model.actor_list:
            if isinstance(actor, volume_class):
                return actor

        return None
