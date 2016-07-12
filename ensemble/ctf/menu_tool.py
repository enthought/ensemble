from enable.component import Component
from enable.tools.pyface.context_menu_tool import ContextMenuTool
from pyface.action.api import Action, Group, MenuManager
from traits.api import HasTraits, Instance, List


def menu_tool_with_actions(component, actions):
    """ Return a ContextMenuTool for `component` with the given actions.
    """
    return FunctionMenuTool(component, actions=actions)


class FunctionMenuTool(ContextMenuTool):
    actions = List(Instance(HasTraits))

    def _menu_manager_default(self):
        return MenuManager(Group(*self.actions))


class RemoveComponentAction(Action):
    """ Removes a component from the editor.
    """
    name = 'Remove Node'
    component = Instance(Component)

    def perform(self, event):
        component = self.component
        if component.removable:
            editor = component.container
            editor.remove_function_component(component)
