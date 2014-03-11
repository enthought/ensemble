from enaml.colors import Color
import traits_enaml

with traits_enaml.imports():
    from enaml.widgets.api import FileDialogEx
    from enaml.widgets.color_dialog import ColorDialog


def get_color(starting_color=None):
    """ Show a color picker to the user and return the color which is selected.

    If no color is selected (because the user cancels the dialog), return None.
    """
    def color_as_tuple(color):
        return (color.red/255., color.green/255., color.blue/255.)

    def tuple_as_color(tup):
        r, g, b = tup
        return Color(int(r * 255), int(g * 255), int(b * 255), 255)

    dlg_kwargs = {'show_alpha': False}
    if starting_color:
        dlg_kwargs['current_color'] = tuple_as_color(starting_color)

    color = ColorDialog.get_color(**dlg_kwargs)
    return None if color is None else color_as_tuple(color)


def get_filename(action='save'):
    """ Show a file dialog to the user and return the path of the file which is
    selected.

    If no file is selected (because the user cancels the dialog), return an
    empty string
    """
    function = getattr(FileDialogEx, 'get_' + action + '_file_name')
    return function()
