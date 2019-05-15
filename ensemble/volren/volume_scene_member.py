from __future__ import unicode_literals
from abc import abstractmethod

from traits.api import ABCHasStrictTraits


class ABCVolumeSceneMember(ABCHasStrictTraits):
    """ An abstract base class for object which contribute actors to a mayavi
    scene which contains a `Volume` actor.
    """

    @abstractmethod
    def add_actors_to_scene(self, scene_model, volume_actor):
        """ Add actors to the mayavi scene `scene_model`.
        """
