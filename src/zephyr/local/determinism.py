"""Audited max-pool equivalent using deterministic gather backward.

MaxPool3d supplies its exact argmax indices; gather preserves its forward
values and tie choice. PyTorch deterministic mode orders repeated-index
gradient accumulation. No weights, precision, or model outputs are changed.
"""
from contextlib import contextmanager
import torch
import torch.nn.functional as F


class _Pool(torch.autograd.Function):
    @staticmethod
    def forward(ctx,x,module):
        values,indices=F.max_pool3d(x,module.kernel_size,module.stride,module.padding,module.dilation,
                                   ceil_mode=module.ceil_mode,return_indices=True)
        ctx.save_for_backward(indices);ctx.shape=x.shape
        ctx.mark_non_differentiable(indices)
        return values,indices

    @staticmethod
    def backward(ctx,gradient,_indices_gradient):
        indices,=ctx.saved_tensors
        result=gradient.new_zeros(ctx.shape)
        previous=torch.are_deterministic_algorithms_enabled()
        warn=torch.is_deterministic_algorithms_warn_only_enabled()
        try:
            # Scope the flag to accumulation only. Global deterministic mode
            # can select different convolution algorithms and change predictions.
            torch.use_deterministic_algorithms(True)
            result.flatten(-3).scatter_add_(-1,indices.flatten(-3),gradient.flatten(-3))
        finally:torch.use_deterministic_algorithms(previous,warn_only=warn)
        return result,None


def pool_with_gather(x, module):
    values,indices=_Pool.apply(x,module)
    return (values, indices) if module.return_indices else values


@contextmanager
def deterministic_pooling(model):
    previous = torch.are_deterministic_algorithms_enabled()
    warn = torch.is_deterministic_algorithms_warn_only_enabled()
    restored=[]
    original_backward=torch.autograd.backward
    def ordered_backward(*args,**kwargs):
        before=torch.are_deterministic_algorithms_enabled()
        before_warn=torch.is_deterministic_algorithms_warn_only_enabled()
        try:
            torch.use_deterministic_algorithms(True)
            return original_backward(*args,**kwargs)
        finally:torch.use_deterministic_algorithms(before,warn_only=before_warn)
    try:
        # Only use this adapter inside the isolated, single-job GPU process.
        torch.autograd.backward=ordered_backward
        for module in model.modules():
            if isinstance(module,torch.nn.MaxPool3d):
                own = module.__dict__.get('forward')
                restored.append((module,own))
                module.forward=lambda x, m=module:pool_with_gather(x,m)
        yield
    finally:
        torch.autograd.backward=original_backward
        for module,own in restored:
            if own is None: del module.forward
            else: module.forward=own
        torch.use_deterministic_algorithms(previous,warn_only=warn)
