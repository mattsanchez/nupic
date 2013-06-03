# ----------------------------------------------------------------------
#  Copyright (C) 2006-2008 Numenta Inc. All rights reserved.
#
#  The information and source code contained herein is the
#  exclusive property of Numenta Inc. No part of this software
#  may be used, reproduced, stored or distributed in any form,
#  without explicit written authorization from Numenta Inc.
# ----------------------------------------------------------------------

from nupic.regions.ImageSensorExplorers.BaseExplorer import BaseExplorer
from nupic.regions.ImageSensorExplorers.SpiralSweep import SpiralSweep

class ToCenterSweep(SpiralSweep):

  """
  This explorer sweeps each image to the left until it reaches the center position.
  For example, if the sweep length is 4 then multiple presentations will be
  generated at the following locations (where 'o' is the center)




           o  x  x  x




  ToCenterSweep sub-classes SpiralSweep, which is provides general-purpose logic
  for explorers that generate multiple translated presentations of each image.
  It overrides the __init__ method where it generates the particular "to center"
  list of offsets (where SpiralSweep generates a spiral-like list of offsets)

  The image is swept horizontally right to left.
  """

  def __init__(self, length=1, stepsize=1, *args, **kwargs):
    """
    length - the distance from the center to the outer x
    stepsize - the distance between the x's
    minradius - distance from the center to the first x

    If the stepsize is greater than 1, then each 'x' in the diagrams above will be
    separated by 'stepsize' pixels. The 'length' must always be a multiple of
    'stepsize'

    """

    assert(length >= 1)
    SpiralSweep.__init__(self, radius=length, stepsize=stepsize, minradius=None,
                          *args, **kwargs)

    # Generate a list of possible offsets for this stepsize and length
    self.offsets = []

    # Generate the horizontal sweep
    for i in range(-length+1, 1, stepsize):
      self.offsets += [(i, 0)]