import numpy as np

from enable.api import ColorTrait, Container
from pyface.action.api import Action
from traits.api import Callable, Either, Instance, Tuple, on_trait_change

from .color_function_component import ColorNode, ColorComponent
from .function_component import FunctionComponent, MINIMUM_RADIUS
from .gaussian_function_component import (GaussianComponent, GaussianColorNode,
                                          GaussianOpacityNode)
from .menu_tool import menu_tool_with_actions
from .opacity_function_component import OpacityNode, OpacityComponent
from .transfer_function import TransferFunction
from .utils import build_screen_to_function


class BaseCtfEditorAction(Action):
    container = Instance(Container)
    screen_to_function = Callable

    def _screen_to_function_default(self):
        return build_screen_to_function(self.container)


class BaseColorAction(BaseCtfEditorAction):
    # A callable which prompts the user for a color
    prompt_color = Callable

    def perform(self, event):
        color = self.prompt_color()
        if color is None:
            return

        self.perform_with_color(event, color)


class AddColorAction(BaseColorAction):
    name = 'Add Color...'

    def perform_with_color(self, event, color):
        screen_position = (event.enable_event.x, 0.0)
        rel_x, _ = self.screen_to_function(screen_position)

        node = ColorNode(center=rel_x, color=color)
        component = ColorComponent(node=node)
        self.container.add_function_component(component)


class AddGaussianAction(BaseColorAction):
    name = 'Add Gaussian...'

    def perform_with_color(self, event, color):
        screen_position = (event.enable_event.x, event.enable_event.y)
        rel_x, rel_y = self.screen_to_function(screen_position)
        rad = MINIMUM_RADIUS

        color_node = GaussianColorNode(center=rel_x, color=color, radius=rad)
        opacity_node = GaussianOpacityNode(center=rel_x, opacity=rel_y,
                                           radius=rad)
        component = GaussianComponent(node=color_node,
                                      opacity_node=opacity_node)
        self.container.add_function_component(component)


class AddOpacityAction(BaseCtfEditorAction):
    name = 'Add Opacity'

    def perform(self, event):
        screen_position = (event.enable_event.x, event.enable_event.y)
        rel_x, rel_y = self.screen_to_function(screen_position)

        node = OpacityNode(center=rel_x, opacity=rel_y)
        component = OpacityComponent(node=node)
        self.container.add_function_component(component)


class CtfEditor(Container):
    """ A widget for editing transfer functions.
    """

    # The function which is being edited. Contains color and opacity.
    function = Instance(TransferFunction)

    # A callable which prompts the user for a color
    # A single keyword argument 'starting_color' will be passed to the callable
    # and its value will be None or an RGB tuple with values in the range
    # [0, 1]. An RGB tuple should be returned.
    prompt_color_selection = Callable

    # Numpy histogram tuple, if any. (values, bin_edges)
    histogram = Either(Tuple, None)

    # The color to use when drawing the histogram
    histogram_color = ColorTrait('gray')

    # Add some padding to allow mouse interaction near the edge more pleasant.
    padding_left = 5
    padding_bottom = 5
    padding_top = 5
    padding_right = 5
    fill_padding = True

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def add_function_component(self, component):
        self.add(component)
        component.add_function_nodes(self.function)
        component._transfer_function = self.function
        self.function.updated = True
        self.request_redraw()

    def remove_function_component(self, component):
        self.remove(component)
        component.remove_function_nodes(self.function)
        self.function.updated = True
        self.request_redraw()

    # -----------------------------------------------------------------------
    # Traits initialization
    # -----------------------------------------------------------------------

    def _function_default(self):
        function = TransferFunction()
        self._add_components_for_new_function(function)

        return function

    def _tools_default(self):
        prompt_color = self.prompt_color_selection
        actions = [
            AddColorAction(container=self, prompt_color=prompt_color),
            AddGaussianAction(container=self, prompt_color=prompt_color),
            AddOpacityAction(container=self),
        ]
        return [menu_tool_with_actions(self, actions)]

    # -----------------------------------------------------------------------
    # Traits notifications
    # -----------------------------------------------------------------------

    def _bounds_changed(self, old, new):
        super(CtfEditor, self)._bounds_changed(old, new)
        for child in self.components:
            if isinstance(child, FunctionComponent):
                child.parent_changed(self)

    def _function_changed(self, new):
        for child in self.components[:]:
            if isinstance(child, FunctionComponent):
                self.remove(child)

        if new is not None:
            self._add_components_for_new_function(new)

        self.request_redraw()

    @on_trait_change('function:updated')
    def _function_updated(self):
        self.request_redraw()

    def _histogram_changed(self):
        self.request_redraw()

    # -----------------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------------

    def _draw_container_mainlayer(self, gc, *args, **kwargs):
        color_nodes = self.function.color.values()
        alpha_nodes = self.function.opacity.values()

        gc.clear()

        with gc:
            # Move the origin to the lower left padding.
            gc.translate_ctm(self.padding_left, self.padding_bottom)

            self._draw_colors(color_nodes, gc)
            if self.histogram is not None:
                self._draw_histogram(gc)
            self._draw_alpha(alpha_nodes, gc)

    def _draw_alpha(self, alpha_nodes, gc):
        """ Draw the opacity curve.
        """
        w, h = self.width, self.height
        points = [(w * i, h * v) for (i, v) in alpha_nodes]

        with gc:
            gc.set_line_width(1.0)
            gc.set_stroke_color((0.0, 0.0, 0.0, 1.0))
            gc.lines(points)
            gc.stroke_path()

    def _draw_colors(self, color_nodes, gc):
        """ Draw the colorbar.
        """
        w, h = self.width, self.height
        grad_stops = np.array([(x, r, g, b, 1.0)
                               for x, r, g, b in color_nodes])

        with gc:
            gc.rect(0, 0, w, h)
            gc.linear_gradient(0, 0, w, 0, grad_stops, 'pad', 'userSpaceOnUse')
            gc.fill_path()

    def _draw_histogram(self, gc):
        """ Draw the logarithm of the histogram.
        """
        values, bin_edges = self.histogram
        w, h = self.width, self.height
        values = values.astype(float)
        zeros = (values == 0)
        min_nonzero = values[~zeros].min()
        values[zeros] = min_nonzero / 2.0
        log_values = np.log(values)
        log_values -= log_values.min()
        log_values /= log_values.max()

        h_values = log_values * h
        bin_edges = bin_edges - bin_edges.min()
        bin_edges *= w / bin_edges.max()
        x = np.concatenate([bin_edges[:1],
                            np.repeat(bin_edges[1:-1], 2),
                            bin_edges[-1:]])
        y = np.repeat(h_values, 2)
        points = np.column_stack([x, y])

        with gc:
            gc.set_line_width(1.0)
            gc.set_stroke_color(self.histogram_color_)
            gc.lines(points)
            gc.stroke_path()

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def _add_components_for_new_function(self, function):
        linked_colors, linked_opacities = [], []
        if len(function.links) > 0:
            linked_colors, linked_opacities = zip(*function.links)

        for func in (function.color, function.opacity):
            last_index = func.size() - 1
            for idx, node in enumerate(func.nodes):
                if node in linked_colors or node in linked_opacities:
                    continue
                component = FunctionComponent.from_function_nodes(node)
                component._transfer_function = function
                component.removable = (idx not in (0, last_index))
                self.add(component)

        for node_pair in function.links:
            component = FunctionComponent.from_function_nodes(*node_pair)
            component._transfer_function = function
            self.add(component)
