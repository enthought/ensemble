from traits.api import Callable, Enum, Float, Instance, on_trait_change

from .base_color_function_component import BaseColorComponent, ColorNode
from .function_component import register_function_component_class
from .function_node import FunctionNode, register_function_node_class
from .movable_component import MovableComponent
from .utils import clip_to_unit


HEIGHT_WIDGET_THICKNESS = 6.0
RESIZE_THRESHOLD = 7.0
BLACK = (0.0, 0.0, 0.0, 1.0)
GRAY = (0.6, 0.6, 0.6, 1.0)
POINTER_MAP = {'move': 'hand', 'resize': 'size left'}


def _get_node(nodes, node_class):
    for node in nodes:
        if isinstance(node, node_class):
            return node
    return None


class GaussianColorNode(ColorNode):
    """ A `ColorNode` representing a single color with a radius.
    """
    def values(self):
        start_x, end_x = self.center - self.radius, self.center + self.radius
        return [(start_x,) + self.color, (end_x,) + self.color]


class GaussianOpacityNode(FunctionNode):
    """ A `FunctionNode` representing opacity with a Gaussian shape.
    """
    # The maximum opacity for this node
    max_opacity = Float

    def copy(self):
        obj = super(GaussianOpacityNode, self).copy()
        obj.max_opacity = self.max_opacity
        return obj

    @classmethod
    def from_dict(cls, dictionary):
        """ Create an instance from the data in `dictionary`.
        """
        return cls(center=dictionary['center'], radius=dictionary['radius'],
                   max_opacity=dictionary['max_opacity'])

    def to_dict(self):
        """ Create a dictionary which represents the state of the node.
        """
        dictionary = super(GaussianOpacityNode, self).to_dict()
        dictionary['max_opacity'] = self.max_opacity
        return dictionary

    def values(self):
        center, radius = self.center, self.radius
        return [(center - radius, 0.0), (center, self.max_opacity),
                (center + radius, 0.0)]


class GaussianHeightWidget(MovableComponent):
    """ A widget for setting the `max_opacity` of a `GaussianOpacityNode`.
    """
    node = Instance(GaussianOpacityNode)

    screen_to_relative = Callable
    relative_to_screen = Callable

    def move(self, delta_x, delta_y):
        opacity = self.node.max_opacity
        _, rel_y = self.screen_to_relative(delta_x, delta_y)
        self.node.max_opacity = clip_to_unit(opacity + rel_y)

        self._sync_component_position()
        self.request_redraw()

    def parent_changed(self, parent):
        self._sync_component_position()
        self.bounds = (parent.bounds[0], HEIGHT_WIDGET_THICKNESS)

    def _draw_overlay(self, gc, *args, **kwargs):
        x, y = self.position
        w, h = self.bounds
        with gc:
            gc.set_stroke_color(BLACK)
            gc.set_fill_color(GRAY)
            gc.rect(x, y, w, h)
            gc.draw_path()

    def _sync_component_position(self):
        if self.container.container is not None:
            _, screen_y = self.relative_to_screen(0.0, self.node.max_opacity)
            self.position = (0.0, screen_y - HEIGHT_WIDGET_THICKNESS/2.0)


class GaussianComponent(BaseColorComponent):
    """ A `BaseColorComponent` which has some radius and both color and
    opacity, with the opacity determined by a Gaussian.
    """

    # The opacity node
    opacity_node = Instance(GaussianOpacityNode)

    # The widget for setting the opacity peak
    opacity_widget = Instance(GaussianHeightWidget)

    # Are we being moved or resized?
    interaction_state = Enum('move', 'resize')

    def __init__(self, **traits):
        super(GaussianComponent, self).__init__(**traits)

        self.opacity_widget = GaussianHeightWidget(
            node=self.opacity_node,
            screen_to_relative=self.screen_to_relative,
            relative_to_screen=self.relative_to_screen,
        )
        self.add(self.opacity_widget)

        self.node.sync_trait('center', self.opacity_node)
        self.node.sync_trait('radius', self.opacity_node)

    def add_function_nodes(self, linked_function):
        """ Add the node(s) for this component.
        """
        linked_function.add_linked_nodes(self.node, self.opacity_node)

    def draw_contents(self, gc):
        """ Draw the component.
        """
        # Nothing.

    @classmethod
    def from_function_nodes(cls, *nodes):
        """ Create an instance from `nodes`.
        """
        color_node = _get_node(nodes, GaussianColorNode)
        opacity_node = _get_node(nodes, GaussianOpacityNode)
        if len(nodes) != 2 and (color_node is None or opacity_node is None):
            raise ValueError('Expecting two Gaussian function nodes!')

        return cls(node=color_node, opacity_node=opacity_node)

    def move(self, delta_x, delta_y):
        """ Move the component.
        """
        rel_x, _ = self.screen_to_relative(delta_x, 0.0)

        if self.interaction_state == 'move':
            center = self.node.center
            self.set_node_center(self.node, center + rel_x)
        elif self.interaction_state == 'resize':
            # XXX: Resize is only on the left side of the component for now.
            # Some debugging will need to happen to get it working on the right
            # side too.
            radius = self.node.radius
            self.set_node_radius(self.node, radius - rel_x)
            self._sync_component_bounds()
            self.opacity_widget.parent_changed(self)

        self._sync_component_position()

    def node_limits(self, linked_function):
        """ Compute the movement bounds of the function node.
        """
        color_limits = linked_function.color.node_limits(self.node)
        opacity_limits = linked_function.opacity.node_limits(self.opacity_node)
        color_radius = self.node.radius
        opacity_radius = self.opacity_node.radius
        return (max(color_limits[0] + color_radius,
                    opacity_limits[0] + opacity_radius),
                min(color_limits[1] - color_radius,
                    opacity_limits[1] - opacity_radius))

    def parent_changed(self, parent):
        """ Called when the parent of this component changes instances or
        bounds.
        """
        self._sync_component_bounds()
        self._sync_component_position()

        for child in self.components:
            child.parent_changed(self)

    def remove_function_nodes(self, linked_function):
        """ Remove the node(s) for this component.
        """
        linked_function.remove_linked_nodes(self.node, self.opacity_node)

    # -----------------------------------------------------------------------
    # Enable component methods
    # -----------------------------------------------------------------------

    def normal_mouse_move(self, event):
        real_x = event.x - self.container.padding_left
        relative_x, _ = self.get_relative_coords(real_x, 0.0)
        if relative_x < RESIZE_THRESHOLD:
            self.interaction_state = 'resize'
        else:
            self.interaction_state = 'move'

        event.window.set_pointer(POINTER_MAP[self.interaction_state])

    def normal_mouse_leave(self, event):
        event.window.set_pointer('arrow')

    # -----------------------------------------------------------------------
    # Traits methods
    # -----------------------------------------------------------------------

    @on_trait_change('opacity_node.max_opacity')
    def _node_values_changed(self):
        if not self.traits_inited():
            return

        self.update_function()
        self.request_redraw()

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def _sync_component_bounds(self):
        center, radius = self.node.center, self.node.radius
        start_x, height = self.relative_to_screen(center - radius, 1.0)
        end_x, _ = self.relative_to_screen(center + radius, 1.0)
        self.bounds = (end_x - start_x, height)

    def _sync_component_position(self):
        center, radius = self.node.center, self.node.radius
        screen_x, _ = self.relative_to_screen(center - radius, 0.0)
        self.position = (screen_x, 0.0)


# Register our function node
register_function_node_class(GaussianColorNode)
register_function_node_class(GaussianOpacityNode)
# ... and our function component
register_function_component_class(GaussianColorNode, GaussianComponent)
register_function_component_class(GaussianOpacityNode, GaussianComponent)
