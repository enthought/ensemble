"""
This demonstrates the `CtfEditor` widget.

To use: right-click in the window to bring up a context menu. Once you've added
a color or opacity, you can drag them around by just clicking on them. The
colors at the end points are editable, but cannot be removed.

"""

from os.path import join

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

from enaml.qt.qt_application import QtApplication
from ensemble.ctf.api import CtfEditor, CtfManager, get_color
import traits_enaml


if __name__ == "__main__":
    with traits_enaml.imports():
        from ctf_demo_window import CtfDemoWindow

    app = QtApplication()

    ctf_editor = CtfEditor(prompt_color_selection=get_color)
    ctf_manager = CtfManager.from_directory(
        join(ETSConfig.application_data, 'CTF_demo')
    )
    win = CtfDemoWindow(ctf_editor=ctf_editor, ctf_manager=ctf_manager)
    win.show()

    app.start()
