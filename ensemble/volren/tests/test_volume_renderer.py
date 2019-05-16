from __future__ import division, unicode_literals

import os
import unittest

import numpy as np
import six

import vtk
from traits_enaml.testing.enaml_test_assistant import EnamlTestAssistant
from tvtk.api import tvtk

from ensemble.volren.volume_axes import VolumeAxes
from ensemble.volren.volume_bounding_box import VolumeBoundingBox
from ensemble.volren.volume_cut_planes import VolumeCutPlanes
from ensemble.volren.volume_data import VolumeData
from ensemble.volren.volume_viewer import VolumeViewer, CLIP_MAX


AXES_ACTOR_CLASS = tvtk.CubeAxesActor
CUT_PLANE_ACTOR_CLASS = tvtk.ImagePlaneWidget
CLIP_BOUNDS = [0, CLIP_MAX/2, 0, CLIP_MAX/2, 0, CLIP_MAX/2]
VTK_MAJOR_VERSION = vtk.vtkVersion.GetVTKMajorVersion()


def count_types(type_class, obj_list):
    return sum(int(isinstance(obj, type_class)) for obj in obj_list)


# We use a newer version of VTK (8) which needs a newer version of OpenGL 3.2
# which is not available on Travis CI at the moment
@unittest.skipIf(os.environ.get('IS_CI', None), "Travis OpenGL issues")
class VolumeViewerTestCase(EnamlTestAssistant, unittest.TestCase):

    def setUp(self):

        EnamlTestAssistant.setUp(self)

        enaml_source = """
from enaml.widgets.api import Container
from ensemble.volren.volume_viewer_ui import VolumeViewerContainer

enamldef MainView(Container): view:
    attr viewer

    VolumeViewerContainer:
        viewer << view.viewer

"""
        if six.PY2:
            enaml_source = enaml_source.encode('utf-8')
        volume = np.random.normal(size=(32, 32, 32))
        volume = (255*(volume-volume.min())/volume.ptp()).astype(np.uint8)
        volume_data = VolumeData(raw_data=volume)
        volume_axes = VolumeAxes(visible_axis_scales=(True, True, True))
        volume_bbox = VolumeBoundingBox()
        volume_cut_planes = VolumeCutPlanes()
        scene_members = {'axes': volume_axes, 'bbox': volume_bbox,
                         'cut_planes': volume_cut_planes}
        self.viewer = VolumeViewer(volume_data=volume_data,
                                   scene_members=scene_members,
                                   clip_bounds=CLIP_BOUNDS)
        self.view, _ = self.parse_and_create(enaml_source,
                                             viewer=self.viewer)

        with self.event_loop():
            self.view.show()

    def tearDown(self):
        self.view.destroy()
        self.view = None
        self.viewer = None
        EnamlTestAssistant.tearDown(self)

    def _example_volume_mask(self, volume_array):
        """
           Generates a sample mask given the raw volume data.
        """
        mask = np.zeros_like(volume_array)
        depth, height, width = mask.shape
        half = (depth // 2, height // 2, width // 2)
        quarter = (depth // 4, height // 4, width // 4)
        axis_slices = [slice(half[i]-quarter[i], half[i]+quarter[i])
                       for i in range(3)]
        mask[axis_slices[0], axis_slices[1], axis_slices[2]] = 255
        return mask

    def test_renderer_initialized(self):
        self.assertTrue(self.viewer.volume_renderer.volume is not None)
        volume_mapper = self.viewer.volume_renderer.volume._volume_mapper
        if VTK_MAJOR_VERSION > 6:
            self.assertIsInstance(volume_mapper, tvtk.SmartVolumeMapper)
            self.assertEqual(volume_mapper.requested_render_mode, 'default')
        else:
            self.assertNotIsInstance(volume_mapper, tvtk.SmartVolumeMapper)

        # Count various actor types in the scene.
        scene_model = self.viewer.model
        axes_count = count_types(AXES_ACTOR_CLASS, scene_model.renderer.actors)
        cutplane_count = count_types(CUT_PLANE_ACTOR_CLASS,
                                     scene_model.actor_list)

        # Ensure bounding box is computed
        outline = self.viewer.scene_members['bbox'].outline
        self.assertEqual(outline.output.number_of_points, 8)

        self.assertEqual(axes_count, 1)
        self.assertEqual(cutplane_count, 3)

    def test_volume_data_masking(self):
        # Test applying mask, Pull Request #44.

        volume_data = self.viewer.volume_data
        volume = volume_data.raw_data

        # Mask is not set initially
        points_without_mask = volume_data.render_data.number_of_points
        # 256^3: that's because we are resampling the data before sending it
        # to VTK, see `volume_data._resample_data`.
        self.assertEqual(points_without_mask, 256 * 256 * 256)

        # Now apply mask
        mask_data = self._example_volume_mask(volume)
        self.viewer.volume_data.mask_data = mask_data
        points_with_mask = volume_data.render_data.number_of_points
        self.assertEqual(points_with_mask, mask_data.size)

    def test_renderer_clipping_bounds(self):
        self.assertEqual(self.viewer.volume_renderer.clip_bounds, CLIP_BOUNDS)

    def test_renderer_screenshot(self):
        # With default resolution
        image_array = self.viewer.screenshot()
        s1 = image_array.size
        self.assertTrue(image_array.ndim == 3)
        self.assertTrue(image_array.shape[-1] == 3)

        # With higher resolution
        magnification = 3
        image_array = self.viewer.screenshot(magnification=magnification)
        s2 = image_array.size
        self.assertTrue(image_array.ndim == 3)
        self.assertTrue(image_array.shape[-1] == 3)
        self.assertEqual(s2 / s1, magnification * magnification)

    def test_data_update(self):
        # Changing the raw data should update the `vmin` and `vmax` values
        new_volume = 42 * np.ones_like(self.viewer.volume_data.raw_data)
        new_min = 10
        new_max = 100
        new_volume[0, 0, 0] = new_min
        new_volume[-1, -1, -1] = new_max

        self.viewer.volume_renderer.data.raw_data = new_volume

        self.assertEqual(self.viewer.volume_renderer.vmin, new_min)
        self.assertEqual(self.viewer.volume_renderer.vmax, new_max)


if __name__ == "__main__":
    unittest.main()
