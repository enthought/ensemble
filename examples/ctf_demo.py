"""
This demonstrates the `CtfEditor` widget.

To use: right-click in the window to bring up a context menu. Once you've added
a color or opacity, you can drag them around by just clicking on them. The
colors at the end points are editable, but cannot be removed.

"""

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

from enaml.qt.qt_application import QtApplication
from ensemble.ctf.editor import CtfEditor
from ensemble.ctf.gui_utils import get_color
import traits_enaml

if __name__ == "__main__":
    with traits_enaml.imports():
        from ctf_demo_window import CtfDemoWindow

    app = QtApplication()

    ctf = CtfEditor(prompt_color_selection=get_color)
    win = CtfDemoWindow(ctf=ctf)
    win.show()

    app.start()
