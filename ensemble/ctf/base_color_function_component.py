from __future__ import unicode_literals
from pyface.action.api import Action
from traits.api import Callable, Float, Instance, Tuple

from .function_component import FunctionComponent
from .function_node import FunctionNode
from .menu_tool import RemoveComponentAction, menu_tool_with_actions
from .transfer_function import TransferFunction


class EditColorAction(Action):
    name = 'Edit Color...'

    # The ColorComponent being edited.
    component = Instance(FunctionComponent)

    # The function where our node lives
    function = Instance(TransferFunction)

    # A callable which prompts the user for a color
    prompt_color = Callable

    def perform(self, event):
        new_color = self.prompt_color()
        if new_color is None:
            return

        self.component.node.color = new_color
        self.function.updated = True


class ColorNode(FunctionNode):
    """ A `FunctionNode` representing a single color.
    """

    # Infinitely thin!
    radius = 0.0

    # The color for this node
    color = Tuple(Float, Float, Float)

    def copy(self):
        obj = super(ColorNode, self).copy()
        obj.color = self.color
        return obj

    @classmethod
    def from_dict(cls, dictionary):
        """ Create an instance from the data in `dictionary`.
        """
        return cls(center=dictionary['center'], radius=dictionary['radius'],
                   color=tuple(dictionary['color']))

    def to_dict(self):
        """ Create a dictionary which represents the state of the node.
        """
        dictionary = super(ColorNode, self).to_dict()
        dictionary['color'] = self.color
        return dictionary

    def values(self):
        return [(self.center,) + self.color]


class BaseColorComponent(FunctionComponent):
    """ A base class for `FunctionComponent` objects which need to edit colors.

    Really, it just handles the common context menu code.
    """

    def _tools_default(self):
        prompt_color = self.container.prompt_color_selection
        function = self.container.function
        actions = [
            EditColorAction(component=self, function=function,
                            prompt_color=prompt_color),
            RemoveComponentAction(component=self),
        ]
        return [menu_tool_with_actions(self, actions)]
