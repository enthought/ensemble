import unittest

import numpy as np

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


def count_types(type_class, obj_list):
    return sum(int(isinstance(obj, type_class)) for obj in obj_list)


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
        self.view = None
        self.viewer = None
        EnamlTestAssistant.tearDown(self)

    def _example_volume_mask(self, volume_array):
        """
           Generates a sample mask given the raw volume data.
        """
        mask = np.zeros_like(volume_array)
        depth, height, width = mask.shape
        half = (depth/2, height/2, width/2)
        quarter = (depth/4, height/4, width/4)
        axis_slices = [slice(half[i]-quarter[i], half[i]+quarter[i])
                       for i in range(3)]
        mask[axis_slices[0], axis_slices[1], axis_slices[2]] = 255
        return mask

    def test_renderer_initialized(self):
        self.assertTrue(self.viewer.volume_renderer.volume is not None)

        # Count various actor types in the scene.
        # XXX: The actor class for `VolumeBoundingBox` is too generic to be
        # counted.
        scene_model = self.viewer.model
        axes_count = count_types(AXES_ACTOR_CLASS, scene_model.renderer.actors)
        cutplane_count = count_types(CUT_PLANE_ACTOR_CLASS,
                                     scene_model.actor_list)

        self.assertEqual(axes_count, 1)
        self.assertEqual(cutplane_count, 3)

        # Test applying mask, Pull Request #44
        # Mask is not set initially
        volume_data = self.viewer.volume_data
        points_without_mask = volume_data.render_data.number_of_points
        self.assertGreater(points_without_mask, 0)
        # Now apply mask
        volume = volume_data.raw_data
        mask_data = self._example_volume_mask(volume)
        self.viewer.volume_data.mask_data = mask_data
        points_with_mask = volume_data.render_data.number_of_points
        self.assertGreater(points_without_mask, points_with_mask)

    def test_renderer_clipping_bounds(self):
        self.assertEqual(self.viewer.volume_renderer.clip_bounds, CLIP_BOUNDS)

    def test_renderer_screenshot(self):
        image_array = self.viewer.screenshot()
        self.assertTrue(image_array.ndim == 3)
        self.assertTrue(image_array.shape[-1] == 3)

if __name__ == "__main__":
    unittest.main()
