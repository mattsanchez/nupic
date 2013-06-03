#!/usr/bin/env python
# ----------------------------------------------------------------------
# Copyright (C) 2012, Numenta Inc. All rights reserved.
#
# The information and source code contained herein is the
# exclusive property of Numenta Inc.  No part of this software
# may be used, reproduced, stored or distributed in any form,
# without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

"""Unit tests for aggregator module."""

import unittest2 as unittest

from nupic.data import aggregator


class AggregatorTest(unittest.TestCase):
  """Unit tests for misc. aggregator functions."""

  def testFixAggregationDict(self):
    # Simplest case.
    result = aggregator._aggr_weighted_mean((1.0, 1.0), (1, 1))
    self.assertAlmostEqual(result, 1.0, places=7)
    # Simple non-uniform case.
    result = aggregator._aggr_weighted_mean((1.0, 2.0), (1, 2))
    self.assertAlmostEqual(result, 5.0/3.0, places=7)
    # Make sure it handles integer values as integers.
    result = aggregator._aggr_weighted_mean((1, 2), (1, 2))
    self.assertAlmostEqual(result, 1, places=7)
    # More-than-two case.
    result = aggregator._aggr_weighted_mean((1.0, 2.0, 3.0), (1, 2, 3))
    self.assertAlmostEqual(result, 14.0/6.0, places=7)
    # Handle zeros.
    result = aggregator._aggr_weighted_mean((1.0, 0.0, 3.0), (1, 2, 3))
    self.assertAlmostEqual(result, 10.0/6.0, places=7)
    # Handle negative numbers.
    result = aggregator._aggr_weighted_mean((1.0, -2.0, 3.0), (1, 2, 3))
    self.assertAlmostEqual(result, 1.0, places=7)


if __name__ == '__main__':
  unittest.main()