from __future__ import division
from __future__ import print_function
import os
import sys
import math
import numpy as np
import copy
from _Ax import Ax
from _Atb import Atb
from tigre.Utilities.filtering import filtering
import scipy.io

# TODO: this is quite nasty; it would be nice to reorganise file structure later so top level folder is always in path
currDir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.abspath(os.path.join(currDir, '..'))
if rootDir not in sys.path:  # add parent dir to paths
    sys.path.append(rootDir)

def FDK(proj, geo, angles,filter=None):

    if filter is not None:
        geo.filter=filter
    # Weight
    proj=proj.transpose()
    proj=proj.transpose(0,2,1)

    for ii in range(len(angles)):
        xv=np.arange((-geo.nDetector[0]/2)+0.5, 1+(geo.nDetector[0]/2)-0.5)*geo.dDetector[0]
        yv=np.arange((-geo.nDetector[1]/2)+0.5, 1+(geo.nDetector[1]/2)-0.5)*geo.dDetector[1]
        (xx, yy) = np.meshgrid(xv, yv)

        w = geo.DSD/np.sqrt((geo.DSD ** 2 + xx ** 2 + yy ** 2))
        proj[ii] = proj[ii]*w.transpose()


    proj_filt=filtering(proj.transpose(0,2,1),geo,angles,parker=False).transpose()
    # m = {
    #     'py_projfilt': proj_filt,
    #
    # }
    # scipy.io.savemat('Tests/Filter_data', m)
    return Atb(proj_filt,geo,angles,'FDK')
