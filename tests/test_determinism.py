import unittest
import torch
from zephyr.local.determinism import deterministic_pooling


class PoolTests(unittest.TestCase):
    def test_exact_forward_and_backward_including_ties_and_overlap(self):
        for device in ['cpu']+(['cuda'] if torch.cuda.is_available() else []):
            for stride in (1,2):
                torch.manual_seed(17)
                # Integer values deliberately produce ties and repeated argmax indices.
                x=torch.randint(0,4,(2,3,6,6,6),device=device).float().requires_grad_()
                model=torch.nn.Sequential(torch.nn.MaxPool3d(3,stride=stride,padding=1,ceil_mode=True))
                y=model(x);weights=torch.randn_like(y);y.backward(weights);expected=x.grad.clone();x.grad=None
                old=torch.are_deterministic_algorithms_enabled()
                with deterministic_pooling(model):
                    actual=model(x);self.assertTrue(torch.equal(y,actual));actual.backward(weights)
                torch.testing.assert_close(x.grad,expected,rtol=1e-5,atol=1e-5)
                self.assertEqual(old,torch.are_deterministic_algorithms_enabled())
                self.assertNotIn('forward',model[0].__dict__)
