from enable.component import Component
from enable.tools.pyface.context_menu_tool import ContextMenuTool
from pyface.action.api import Action, Group, MenuManager, Separator
from traits.api import Callable, Instance, List, Type

from ensemble.ctf.piecewise import PiecewiseFunction
from ensemble.ctf.utils import (FunctionUIAdapter, AlphaFunctionUIAdapter,
                                ColorFunctionUIAdapter, load_ctf, save_ctf)


class BaseCtfAction(Action):
    component = Instance(Component)
    function = Instance(PiecewiseFunction)
    ui_adaptor = Instance(FunctionUIAdapter)
    ui_adaptor_klass = Type

    def _ui_adaptor_default(self):
        return self.ui_adaptor_klass(component=self.component,
                                     function=self.function)

    def _get_relative_event_position(self, event):
        return self.ui_adaptor.screen_to_function((event.x, event.y))


class AddColorAction(BaseCtfAction):
    name = 'Add Color...'
    ui_adaptor_klass = ColorFunctionUIAdapter

    # A callable which prompts the user for a color
    prompt_color = Callable

    def perform(self, event):
        pos = self._get_relative_event_position(event.enable_event)
        new_color = self.prompt_color()
        if new_color is not None:
            color_val = (pos[0],) + new_color
            self.component.add_function_node(self.function, color_val)


class AddOpacityAction(BaseCtfAction):
    name = 'Add Opacity'
    ui_adaptor_klass = AlphaFunctionUIAdapter

    def perform(self, event):
        pos = self._get_relative_event_position(event.enable_event)
        self.component.add_function_node(self.function, pos)


class EditColorAction(BaseCtfAction):
    name = 'Edit Color...'
    ui_adaptor_klass = ColorFunctionUIAdapter

    # A callable which prompts the user for a color
    prompt_color = Callable

    def perform(self, event):
        mouse_pos = (event.enable_event.x, event.enable_event.y)
        index = self.ui_adaptor.function_index_at_position(*mouse_pos)
        if index is not None:
            color_val = self.function.value_at(index)
            edited_color = self.prompt_color(color_val[1:])
            if edited_color is not None:
                new_value = (color_val[0],) + edited_color
                self.component.edit_function_node(self.function, index,
                                                  new_value)


class RemoveNodeAction(Action):
    """ Removes a node from one of the functions.
    """
    name = 'Remove Node'
    component = Instance(Component)
    alpha_func = Instance(PiecewiseFunction)
    color_func = Instance(PiecewiseFunction)
    ui_adaptors = List(Instance(FunctionUIAdapter))

    def _ui_adaptors_default(self):
        # Alpha function first so that it will take precedence in removals.
        return [AlphaFunctionUIAdapter(component=self.component,
                                       function=self.alpha_func),
                ColorFunctionUIAdapter(component=self.component,
                                       function=self.color_func)]

    def perform(self, event):
        mouse_pos = (event.enable_event.x, event.enable_event.y)
        for adaptor in self.ui_adaptors:
            index = adaptor.function_index_at_position(*mouse_pos)
            if index is not None:
                self.component.remove_function_node(adaptor.function, index)
                return


class LoadFunctionAction(Action):
    name = 'Load Function...'
    component = Instance(Component)
    alpha_func = Instance(PiecewiseFunction)
    color_func = Instance(PiecewiseFunction)

    # A callable which prompts the user for a filename
    prompt_filename = Callable

    def perform(self, event):
        filename = self.prompt_filename(action='open')
        if len(filename) == 0:
            return

        color_func, alpha_func = load_ctf(filename)
        funcs = ((self.alpha_func, alpha_func), (self.color_func, color_func))
        for dest, source in funcs:
            dest.clear()
            for value in source.items():
                dest.insert(value)
        self.component.update_function()


class SaveFunctionAction(Action):
    name = 'Save Function...'
    component = Instance(Component)
    alpha_func = Instance(PiecewiseFunction)
    color_func = Instance(PiecewiseFunction)

    # A callable which prompts the user for a filename
    prompt_filename = Callable

    def perform(self, event):
        filename = self.prompt_filename(action='save')
        if len(filename) == 0:
            return
        save_ctf(self.color_func, self.alpha_func, filename)


class FunctionMenuTool(ContextMenuTool):
    def _menu_manager_default(self):
        component = self.component
        alpha_func = component.opacities
        color_func = component.colors
        prompt_color = component.prompt_color_selection
        prompt_filename = component.prompt_file_selection
        return MenuManager(
            Group(
                AddColorAction(component=component, function=color_func,
                               prompt_color=prompt_color),
                AddOpacityAction(component=component, function=alpha_func),
                id='AddGroup',
            ),
            Separator(),
            Group(
                EditColorAction(component=component, function=color_func,
                                prompt_color=prompt_color),
                id='EditGroup',
            ),
            Separator(),
            Group(
                RemoveNodeAction(component=component, alpha_func=alpha_func,
                                 color_func=color_func),
                id='RemoveGroup',
            ),
            Separator(),
            Group(
                LoadFunctionAction(component=component, alpha_func=alpha_func,
                                   color_func=color_func,
                                   prompt_filename=prompt_filename),
                SaveFunctionAction(component=component, alpha_func=alpha_func,
                                   color_func=color_func,
                                   prompt_filename=prompt_filename),
                id='IOGroup',
            ),
        )
