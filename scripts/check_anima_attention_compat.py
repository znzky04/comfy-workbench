"""Check installed Anima reference attention without loading models or starting ComfyUI.

Run with the ComfyUI Python environment, which already provides torch.
The tested functions and container class are extracted from the installed source.
"""

import ast
import functools
import os
import unittest
from pathlib import Path
from types import SimpleNamespace

import torch
import torch.nn.functional as F

ROOT = Path(os.environ.get("COMFYUI_TEST_ROOT", "E:/AI/ComfyUI-Workspace/ComfyUI/ComfyUI"))


def definitions(path, names, namespace):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    selected = [node for node in tree.body if getattr(node, "name", None) in names]
    if len(selected) != len(names):
        raise AssertionError(f"Missing definitions in {path}: {names}")
    # Execute only selected definitions from the explicitly selected local installation.
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102


class AttentionCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        core = {"torch": torch, "functools": functools}
        definitions(
            ROOT / "comfy/ldm/modules/attention.py",
            {"AttentionTensorContainer", "wrap_attn"},
            core,
        )
        node = {"torch": torch, "F": F}
        definitions(
            ROOT / "custom_nodes/comfyui-anima-incontext/incontext.py",
            {"make_ref_attn_op"},
            node,
        )
        cls.container = core["AttentionTensorContainer"]
        cls.wrap_attn = staticmethod(core["wrap_attn"])
        cls.make_op = staticmethod(node["make_ref_attn_op"])

    def tensors(self, sequence=4):
        generator = torch.Generator().manual_seed(731)
        return [torch.randn(2, sequence, 2, 3, generator=generator) for _ in range(3)]

    def state(self, active=True, neutral=False):
        bias = torch.tensor([0.4, -1e9])
        mask = torch.zeros(2, 1, 1, 4)
        mask[:, 0, 0, 2:] = bias[:, None]
        return SimpleNamespace(
            active=active,
            bias_B=None if neutral else bias,
            total_tokens=4,
            bias_for=lambda device, dtype: mask.to(device=device, dtype=dtype),
        )

    def check_active(self, containers):
        tensors = self.tensors()
        inputs = [self.container(t) for t in tensors] if containers else tensors
        state = self.state()
        fallback_calls = []

        def fallback(*args, **kwargs):
            fallback_calls.append(args)
            raise AssertionError("Active reference bias must not fall back")

        result = self.make_op(state, fallback)(*inputs, preferred_attention=object())
        q, k, v = [t.transpose(1, 2) for t in tensors]
        expected = F.scaled_dot_product_attention(
            q, k, v, attn_mask=state.bias_for(q.device, q.dtype)
        ).transpose(1, 2).reshape(2, 4, 6)
        torch.testing.assert_close(result, expected)
        self.assertEqual(fallback_calls, [])
        if containers:
            for item in inputs:
                with self.assertRaisesRegex(RuntimeError, "consumed"):
                    item.peek()

    def test_active_containers_preserve_reference_bias(self):
        self.check_active(containers=True)

    def test_active_plain_tensors_remain_supported(self):
        self.check_active(containers=False)

    def check_fallback(self, state, sequence=4):
        inputs = [self.container(t) for t in self.tensors(sequence)]
        options = {"sentinel": object()}
        preferred = object()
        result = object()

        def fallback(q, k, v, transformer_options, **kwargs):
            self.assertIs(q, inputs[0])
            self.assertIs(k, inputs[1])
            self.assertIs(v, inputs[2])
            self.assertIs(transformer_options, options)
            self.assertIs(kwargs["preferred_attention"], preferred)
            for item in inputs:
                self.assertIsNotNone(item.peek())
            return result

        actual = self.make_op(state, fallback)(
            *inputs, transformer_options=options, preferred_attention=preferred
        )
        self.assertIs(actual, result)

    def test_inactive_fallback_keeps_containers(self):
        self.check_fallback(self.state(active=False))

    def test_neutral_fallback_keeps_containers(self):
        self.check_fallback(self.state(neutral=True))

    def test_wrong_sequence_fallback_keeps_containers(self):
        self.check_fallback(self.state(), sequence=3)

    def test_fallback_preserves_core_container_override(self):
        inputs = [self.container(t) for t in self.tensors()]
        sentinel = object()
        seen = []

        def backend(*args, **kwargs):
            raise AssertionError("Override should handle this call")

        def override(*args, **kwargs):
            raise AssertionError("Core should use container_function")

        def container_override(q, k, v, **kwargs):
            seen.append((q, k, v))
            for item in (q, k, v):
                item.take()
            return sentinel

        override.container_function = container_override
        fallback = self.wrap_attn(backend)
        actual = self.make_op(self.state(active=False), fallback)(
            *inputs, transformer_options={"optimized_attention_override": override}
        )
        self.assertIs(actual, sentinel)
        self.assertEqual(seen, [tuple(inputs)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
