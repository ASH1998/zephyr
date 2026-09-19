import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np
import torch
from zephyr.local.forward import geometry_encoding_cache, evaluate_forward


class GeometryCacheTests(unittest.TestCase):
    class Encoding(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.calls = 0
        def forward(self, points, grid, sdf):
            self.calls += 1
            return points + grid + sdf

    def test_exact_inputs_reuse_only_within_one_evaluation(self):
        module = self.Encoding().eval()
        inputs = [torch.ones(2) for _ in range(3)]
        stats = {}
        with torch.no_grad(), geometry_encoding_cache(module, stats):
            torch.testing.assert_close(module(*inputs), torch.full((2,), 3.))
            torch.testing.assert_close(module(*(x.clone() for x in inputs)), torch.full((2,), 3.))
            self.assertEqual(module.calls, 1)
            inputs[0][0] = 2  # In-place changes must invalidate, even on the same tensor.
            torch.testing.assert_close(module(*inputs), torch.tensor([4., 3.]))
            self.assertEqual(module.calls, 2)
        self.assertNotIn('forward', module.__dict__)
        with torch.no_grad(), geometry_encoding_cache(module, {}):
            module(*inputs)
        self.assertEqual(module.calls, 3)
        self.assertEqual(stats, {'geometryCalls': 3, 'geometryCacheHits': 1})

    def test_gradient_training_and_failure_paths_restore_module(self):
        module = self.Encoding().eval()
        args = [torch.ones(2) for _ in range(3)]
        with self.assertRaisesRegex(RuntimeError, 'gradients disabled'):
            with geometry_encoding_cache(module, {}):
                module(*args)
        self.assertNotIn('forward', module.__dict__)
        module.train()
        with self.assertRaises(RuntimeError), torch.no_grad(), geometry_encoding_cache(module, {}):
            module(*args)
        self.assertNotIn('forward', module.__dict__)
        module.eval()
        original = module.forward
        module.forward = original
        with self.assertRaisesRegex(ValueError, 'failure'):
            with torch.no_grad(), geometry_encoding_cache(module, {}):
                module(*args)
                raise ValueError('failure')
        self.assertIs(module.forward, original)


class ForwardForceTests(unittest.TestCase):
    def test_multiple_batches_preserve_force_units_order_and_refresh_geometry(self):
        # 8,193 equal-area faces span two batches, with known analytic traction.
        class Datapipe(torch.utils.data.Dataset):
            SURFACE_KEYS = ('surface_areas', 'surface_normals')
            def __init__(self, **kwargs):
                self.out_dict = {'geometry_coordinates': torch.zeros(3, 3)}
                if kwargs['produce_volume_inputs']:
                    raise AssertionError('Unexpected volume preprocessing')
            def __len__(self):
                return 8193
            def __getitem__(self, index):
                return {'surface_areas': torch.tensor(.25),
                        'surface_normals': torch.tensor([1., 0., 0.])}

        class Model(torch.nn.Module):
            output_features_vol = None
            grid_resolution = (2, 2, 2)
            def __init__(self):
                super().__init__()
                self.geo_rep_surface = GeometryCacheTests.Encoding()
            def forward(self, data):
                if torch.is_grad_enabled() or data['geometry_coordinates'].requires_grad:
                    raise AssertionError('Unused gradients enabled')
                torch.testing.assert_close(data['global_params_values'], torch.tensor([[[2.], [3.]]]))
                n = data['surface_areas'].shape[1]
                return None, torch.tensor([2., .5, .25, -.5]).expand(1, n, 4)

        model = Model().eval()
        domino = SimpleNamespace(model=model, device=torch.device('cpu'),
            bounding_box_volume_min_max=None, bounding_box_surface_min_max=None,
            surf_factors=[None, None])
        mesh = SimpleNamespace(points=np.zeros((3, 3), dtype=np.float32),
            cell_data={'Normals': 'stale'}, point_data={'Normals': 'stale'})
        upstream = SimpleNamespace(_unwrap_model=lambda m: m, DesignDatapipe=Datapipe,
                                   unnormalize=lambda values, *_: values)
        progress = []
        with patch.dict('sys.modules', {'main': upstream}):
            result = evaluate_forward(domino, mesh, stream_velocity=2., air_density=3.,
                progress=lambda done, total: progress.append((done, total)))
        # p=24 Pa, shear=(6,3,-6) Pa; force per face=(4.5,-.75,1.5) N.
        np.testing.assert_array_equal(result['aerodynamic_force'], np.array([4.5, -.75, 1.5]) * 8193)
        np.testing.assert_array_equal(result['pred_surf_pressure'], np.full(8193, 24.))
        self.assertEqual(progress, [(0, 2), (1, 2), (2, 2)])
        self.assertNotIn('geometry_sensitivity', result)
        self.assertEqual(mesh.points.dtype, np.float64)
        self.assertNotIn('Normals', mesh.cell_data)
        self.assertNotIn('Normals', mesh.point_data)


if __name__ == '__main__':
    unittest.main()
