import numpy as np

from traits.api import Callable, Enum, Instance, on_trait_change

from .base_color_function_component import BaseColorComponent, ColorNode
from .function_component import register_function_component_class
from .function_node import (register_function_node_class,
                            register_function_node_class_for_back_compat)
from .movable_component import MovableComponent
from .opacity_function_component import OpacityNode
from .utils import clip_to_unit, trapezoid_window


HEIGHT_WIDGET_THICKNESS = 6.0
RESIZE_THRESHOLD = 7.0
BLACK = (0.0, 0.0, 0.0, 1.0)
GRAY = (0.6, 0.6, 0.6, 1.0)
POINTER_MAP = {'move': 'hand', 'resize': 'size left'}
MAX_NUM_SAMPLES = 256
MINIMUM_RADIUS = 0.005


def _get_node(nodes, node_class):
    for node in nodes:
        if isinstance(node, node_class):
            return node
    return None


class WindowColorNode(ColorNode):
    """ A `ColorNode` representing a single color with a radius.
    """
    def values(self):
        start_x, end_x = self.center - self.radius, self.center + self.radius
        return [(start_x,) + self.color, (end_x,) + self.color]


class WindowOpacityNode(OpacityNode):
    """ An `OpacityNode` with a non-zero radius and a trapezoidal shape.
    """
    def values(self):
        center, radius = self.center, self.radius
        num_samples = int(np.round(radius * 2.0 * MAX_NUM_SAMPLES))

        xs = np.linspace(center - radius, center + radius, num_samples)
        ys = trapezoid_window(num_samples) * self.opacity
        return zip(xs, ys)


class WindowHeightWidget(MovableComponent):
    """ A widget for setting the `opacity` of a `WindowOpacityNode`.
    """

    hover_pointer = "size top"

    node = Instance(WindowOpacityNode)

    screen_to_relative = Callable
    relative_to_screen = Callable

    def move(self, delta_x, delta_y):
        opacity = self.node.opacity
        _, rel_y = self.screen_to_relative(delta_x, delta_y)
        self.node.opacity = clip_to_unit(opacity + rel_y)

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
            _, screen_y = self.relative_to_screen(0.0, self.node.opacity)
            self.position = (0.0, screen_y - HEIGHT_WIDGET_THICKNESS/2.0)


class WindowComponent(BaseColorComponent):
    """ A `BaseColorComponent` which has some radius and both color and
    opacity, with the opacity determined by a window function.
    """

    # The opacity node
    opacity_node = Instance(WindowOpacityNode)

    # The widget for setting the opacity peak
    opacity_widget = Instance(WindowHeightWidget)

    # Are we being moved or resized?
    interaction_state = Enum('move', 'resize')

    def __init__(self, **traits):
        super(WindowComponent, self).__init__(**traits)

        self.opacity_widget = WindowHeightWidget(
            node=self.opacity_node,
            screen_to_relative=self.screen_to_relative,
            relative_to_screen=self.relative_to_screen,
        )
        self.add(self.opacity_widget)

        self.node.sync_trait('center', self.opacity_node)
        self.node.sync_trait('radius', self.opacity_node)

    def add_function_nodes(self, transfer_function):
        """ Add the node(s) for this component.
        """
        transfer_function.add_linked_nodes(self.node, self.opacity_node)

    def draw_contents(self, gc):
        """ Draw the component.
        """
        # Nothing.

    @classmethod
    def from_function_nodes(cls, *nodes):
        """ Create an instance from `nodes`.
        """
        color_node = _get_node(nodes, WindowColorNode)
        opacity_node = _get_node(nodes, WindowOpacityNode)
        if len(nodes) != 2 and (color_node is None or opacity_node is None):
            raise ValueError('Expecting two window function nodes!')

        return cls(node=color_node, opacity_node=opacity_node)

    def move(self, delta_x, delta_y):
        """ Move the component.
        """
        rel_x, _ = self.screen_to_relative(delta_x, 0.0)

        if self.interaction_state == 'move':
            self.update_node_center(self.node, rel_x)
        elif self.interaction_state == 'resize':
            # XXX: Resize is only on the left side of the component for now.
            # Some debugging will need to happen to get it working on the right
            # side too.
            self._update_node_radius(self.node, self.node.radius - rel_x)
            self._sync_component_bounds()
            self.opacity_widget.parent_changed(self)

        self._sync_component_position()

    def node_limits(self, transfer_function):
        """ Compute the movement bounds of the function node.
        """
        color_limits = transfer_function.color.node_limits(self.node)
        opacity_limits = transfer_function.opacity.node_limits(
            self.opacity_node
        )
        return (max(color_limits[0], opacity_limits[0]),
                min(color_limits[1], opacity_limits[1]))

    def parent_changed(self, parent):
        """ Called when the parent of this component changes instances or
        bounds.
        """
        self._sync_component_bounds()
        self._sync_component_position()

        for child in self.components:
            child.parent_changed(self)

    def remove_function_nodes(self, transfer_function):
        """ Remove the node(s) for this component.
        """
        transfer_function.remove_linked_nodes(self.node, self.opacity_node)

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
        event.handled = True

    def normal_mouse_leave(self, event):
        event.window.set_pointer('arrow')
        event.handled = True

    # -----------------------------------------------------------------------
    # Traits methods
    # -----------------------------------------------------------------------

    @on_trait_change('opacity_node.opacity')
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

    def _update_node_radius(self, node, rel_rad):
        min_center, max_center = self._center_limits
        center = node.center
        radius_limit = min(center - min_center, max_center - center)
        node.radius = max(min(rel_rad, radius_limit), MINIMUM_RADIUS)


# Register our function node
register_function_node_class(WindowColorNode)
register_function_node_class(WindowOpacityNode)
# REGISTER GAUSSIAN NODES FOR BACKWARD COMPATIBILITY
# XXX: THESE SHOULD BE REMOVED IN THE (NEXT + 1) RELEASE
register_function_node_class_for_back_compat('GaussianColorNode',
                                             WindowColorNode)
register_function_node_class_for_back_compat('GaussianOpacityNode',
                                             WindowOpacityNode)
# ... and our function component
register_function_component_class(WindowColorNode, WindowComponent)
register_function_component_class(WindowOpacityNode, WindowComponent)
