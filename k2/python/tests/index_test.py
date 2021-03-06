#!/usr/bin/env python3
#
# Copyright (c)  2020  Mobvoi Inc.        (authors: Fangjun Kuang)
#
# See ../../../LICENSE for clarification regarding multiple authors

# To run this single test, use
#
#  ctest --verbose -R index_test_py

import unittest

import k2
import torch


class TestIndex(unittest.TestCase):

    def test(self):
        s0 = '''
            0 1 1 0.1
            0 2 2 0.2
            1 2 3 0.3
            2 3 -1 0.4
            3
        '''
        s1 = '''
            0 1 -1 0.5
            1
        '''
        s2 = '''
            0 2 1 0.6
            0 1 2 0.7
            1 3 -1 0.8
            2 1 3 0.9
            3
        '''
        fsa0 = k2.Fsa.from_str(s0).requires_grad_(True)
        fsa1 = k2.Fsa.from_str(s1).requires_grad_(True)
        fsa2 = k2.Fsa.from_str(s2).requires_grad_(True)

        fsa_vec = k2.create_fsa_vec([fsa0, fsa1, fsa2])

        new_fsa21 = k2.index(fsa_vec, torch.tensor([2, 1], dtype=torch.int32))
        assert new_fsa21.shape == (2, None, None)
        assert torch.allclose(
            new_fsa21.arcs.values()[:, :3],
            torch.tensor([
                # fsa 2
                [0, 2, 1],
                [0, 1, 2],
                [1, 3, -1],
                [2, 1, 3],
                # fsa 1
                [0, 1, -1]
            ]).to(torch.int32))

        scale = torch.arange(new_fsa21.scores.numel())
        (new_fsa21.scores * scale).sum().backward()
        assert torch.allclose(fsa0.scores.grad, torch.tensor([0., 0, 0, 0]))
        assert torch.allclose(fsa1.scores.grad, torch.tensor([4.]))
        assert torch.allclose(fsa2.scores.grad, torch.tensor([0., 1., 2., 3.]))

        # now select only a single FSA
        fsa0.scores.grad = None
        fsa1.scores.grad = None
        fsa2.scores.grad = None

        new_fsa0 = k2.index(fsa_vec, torch.tensor([0], dtype=torch.int32))
        assert new_fsa0.shape == (1, None, None)

        scale = torch.arange(new_fsa0.scores.numel())
        (new_fsa0.scores * scale).sum().backward()
        assert torch.allclose(fsa0.scores.grad, torch.tensor([0., 1., 2., 3.]))
        assert torch.allclose(fsa1.scores.grad, torch.tensor([0.]))
        assert torch.allclose(fsa2.scores.grad, torch.tensor([0., 0., 0., 0.]))


if __name__ == '__main__':
    unittest.main()
