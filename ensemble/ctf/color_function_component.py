from pyface.action.api import Action
from traits.api import Callable, Float, Tuple, Instance

from .function_component import (FunctionComponent,
                                 register_function_component_class)
from .function_node import FunctionNode, register_function_node_class
from .linked import LinkedFunction
from .menu_tool import RemoveComponentAction, menu_tool_with_actions


COMPONENT_WIDTH = 6.0


class EditColorAction(Action):
    name = 'Edit Color...'

    # The ColorComponent being edited.
    component = Instance(FunctionComponent)

    # The function where our node lives
    function = Instance(LinkedFunction)

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


class ColorComponent(FunctionComponent):

    def add_function_nodes(self, linked_function):
        """ Add the node(s) for this component.
        """
        linked_function.color.insert(self.node)

    def draw_contents(self, gc):
        """ Draw the component.
        """
        r, g, b = self.node.color
        screen_x, height = self.relative_to_screen(self.node.center, 1.0)

        with gc:
            gc.set_line_width(1.0)
            gc.set_stroke_color((0.0, 0.0, 0.0, 1.0))
            # FIXME: Bad choice of contrasting color for grays.
            opposite_color = (1.0 - r, 1.0 - g, 1.0 - b, 1.0)
            gc.set_fill_color(opposite_color)
            gc.rect(screen_x - COMPONENT_WIDTH/2.0, 0, COMPONENT_WIDTH, height)
            gc.draw_path()

    @classmethod
    def from_function_nodes(cls, *nodes):
        """ Create an instance from `nodes`.
        """
        if len(nodes) > 1 or not isinstance(nodes[0], ColorNode):
            raise ValueError('Expecting a ColorNode instance!')

        return cls(node=nodes[0])

    def move(self, delta_x, delta_y):
        """ Move the component.
        """
        rel_x, _ = self.screen_to_relative(delta_x, 0.0)
        self.set_node_center(self.node.center + rel_x)
        self._sync_component_position()

    def node_limits(self, linked_function):
        """ Compute the movement bounds of the function node.
        """
        return linked_function.color.node_limits(self.node)

    def parent_changed(self, parent):
        """ Called when the CTF editor bounds change.
        """
        self.bounds = (COMPONENT_WIDTH, parent.bounds[1])
        self._sync_component_position()

    def remove_function_nodes(self, linked_function):
        """ Remove the node(s) for this component.
        """
        linked_function.color.remove(self.node)

    # -----------------------------------------------------------------------
    # Traits methods
    # -----------------------------------------------------------------------

    def _tools_default(self):
        prompt_color = self.container.prompt_color_selection
        function = self.container.function
        actions = [
            EditColorAction(component=self, function=function,
                            prompt_color=prompt_color),
            RemoveComponentAction(component=self),
        ]
        return [menu_tool_with_actions(self, actions)]

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def _sync_component_position(self):
        screen_x, _ = self.relative_to_screen(self.node.center, 0.0)
        self.position = (screen_x - COMPONENT_WIDTH/2.0, 0.0)


# Register our function node
register_function_node_class(ColorNode)
# ... and our function component
register_function_component_class(ColorNode, ColorComponent)
