from __future__ import division
from __future__ import print_function
import time
import os
import sys
from Utilities.init_multigrid import init_multigrid
from scipy.linalg import *
import numpy as np
import copy
from _Ax import Ax
from _Atb import Atb
from Utilities.order_subsets import order_subsets
from Utilities.Measure_Quality import Measure_Quality as MQ
import scipy.io
# TODO: this is quite nasty; it would be nice to reorganise file structure later so top level folder is always in path
currDir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.abspath(os.path.join(currDir, '..'))
if rootDir not in sys.path:  # add parent dir to paths
    sys.path.append(rootDir)

from scipy.linalg import *


def OS_SART(proj, geo, alpha, niter,
            blocksize=20, lmbda=1, lmbda_red=0.99, OrderStrategy=None, Quameasopts=None, init=None, verbose=True,noneg=True):
    """
    OS_SART_CBCT solves Cone Beam CT image reconstruction using Oriented Subsets
              Simultaneous Algebraic Reconxtruction Techique algorithm

    OS_SART_CBCT(PROJ,GEO,ALPHA,NITER) solves the reconstruction problem
    using the projection data PROJ taken over ALPHA angles, corresponding
    to the geometry descrived in GEO, using NITER iterations.

    OS_SART_CBCT(PROJ,GEO,ALPHA,NITER,OPT,VAL,...) uses options and values for solving. The
    possible options in OPT are:

    'BlockSize':   Sets the projection block size used simultaneously. If
                   BlockSize = 1 OS-SART becomes SART and if  BlockSize = length(alpha)
                   then OS-SART becomes SIRT. Default is 20.
                   dtype = int

    'lambda':      Sets the value of the hyperparameter. Default is 1
                   dtype=int or float

    'lambda_red':   Reduction of lambda.Every iteration
                    lambda=lambdared*lambda. Default is 0.95
                    dtype= int or float

    'Init':        Describes diferent initialization techniques.
                   'none'     : Initializes the image to zeros (default)
                   'FDK'      : intializes image to FDK reconstrucition
                   'multigrid': Initializes image by solving the problem in
                                small scale and increasing it when relative
                                convergence is reached.
                   'image'    : Initialization using a user specified
                                image. Not recomended unless you really
                                know what you are doing.
                   dtype=float32

    'InitImg'      an image for the 'image' initialization. Avoid.
                   dtype=np.array([],dtype=float32)

    'Verbose'      True or False. Default is True. Gives information about the
                   progress of the algorithm.
    'QualMeas'     Asks the algorithm for a set of quality measurement
                   parameters. Input should contain a string with optional values 'CC',
                   'RMSE','MSSIM' or 'UQI'.
                   dtype = str

                   These will be computed in each iteration.
  'OrderStrategy'  Chooses the subset ordering strategy. Options are
                   'ordered' :uses them in the input order, but divided
                   'random'  : orders them randomply
                   'angularDistance': chooses the next subset with the
                                      biggest angular distance with the ones used.
                    dtype=str

  OUTPUTS:

     [img]                       will output the reconstructed image
                                 dtype=np.array([],dtype=float32)

 --------------------------------------------------------------------------
 --------------------------------------------------------------------------
 This file is part of the TIGRE Toolbox

 Copyright (c) 2015, University of Bath and
                     CERN-European Organization for Nuclear Research
                     All rights reserved.

 License:            Open Source under BSD.
                     See the full license at
                     https://github.com/CERN/TIGRE/license.txt

 Contact:            tigre.toolbox@gmail.com
 Codes:              https://github.com/CERN/TIGRE/
--------------------------------------------------------------------------
 Coded by:           MATLAB (original code): Ander Biguri
                     PYTHON : Sam Loescher, Reuben Lindroos"""

    if verbose == True:
        print('OS_SART algorithm in progress.')

    angleblocks, angle_index = order_subsets(alpha, blocksize, OrderStrategy)


    #     Projection weight:
    #       - fixing the geometry
    #       - making sure there are no infs in W
    geox = copy.deepcopy(geo)
    geox.sVoxel[2] = max(geox.sDetector[1], geox.sVoxel[2])
    geox.nVoxel = np.array([2, 2, 2])
    geox.dVoxel = geox.sVoxel / geox.nVoxel
    W = Ax(np.ones(geox.nVoxel, dtype=np.float32), geox, alpha, "ray-voxel")
    W[W < min(geo.dVoxel / 4)] = np.inf
    W = 1 / W

    geox = None
    #     Back_Proj weight
    #     NOTE: hstack(array,last value) as np.arange does not include upper limit of interval.
    if geo.mode != 'parallel':

        start = geo.sVoxel[1] / 2 - geo.dVoxel[1] / 2 + geo.offOrigin[1]
        stop = -geo.sVoxel[1] / 2 + geo.dVoxel[1] / 2 + geo.offOrigin[1]
        step = -geo.dVoxel[1]
        xv = np.arange(start, stop + step, step)

        start = geo.sVoxel[2] / 2 - geo.dVoxel[2] / 2 + geo.offOrigin[2]
        stop = -geo.sVoxel[2] / 2 + geo.dVoxel[2] / 2 + geo.offOrigin[2]
        step = -geo.dVoxel[2]
        yv = -1 * np.arange(start, stop + step, step)

        (yy, xx) = np.meshgrid(yv, xv)
        xx = np.expand_dims(xx, axis=2)
        yy = np.expand_dims(yy, axis=2)

        A = (alpha + np.pi / 2)
        V = (geo.DSO / (geo.DSO + (yy * np.sin(-A)) - (xx * np.cos(-A)))) ** 2
        V = np.array(V, dtype=np.float32)


    elif geo.mode == 'parallel':
        V = np.ones([len(alpha), geo.nVoxel[1], geo.nVoxel[0]], dtype=np.float32)

    # Set up init parameters
    lq = []

    if init == 'multigrid':
        if verbose == True:
            print('init multigrid in progress...')
            print('default blocksize=1 for init_multigrid(OS_SART)')
        res = init_multigrid(proj, geo, alpha, alg='SART')
        if verbose == True:
            print('init multigrid complete.')
    if init == 'FDK':
        raise ValueError('FDK not implemented as of yet (coming soon)!')

    if type(init) == np.ndarray:
        if (geo.nVoxel == init.shape).all():

            res = init

        else:
            raise ValueError('wrong dimension of array for initialisation')
    elif init == None:
        res = np.zeros(geo.nVoxel, dtype=np.float32)

    # Iterate

    tic = None
    toc = time.clock()
    for i in range(niter):
        if Quameasopts != None:
            res_prev = res
        if verbose == True:
            if i == 1:
                if tic == None:
                    pass
                else:
                    print('Esitmated time until completetion (s): ' + str(niter * (tic - toc)))

        for j in range(len(angleblocks)):
            if blocksize == 1:
                angle = np.array([angleblocks[j]], dtype=np.float32)
                sumax = 0
                dim_exp=True
            else:
                angle = angleblocks[j]
                sumax = 3
                dim_exp=False

            # PRESENT FOR LOOP
            res += lmbda * 1 / np.array(np.sum(np.expand_dims(
                V[:,:,angle_index[j]], axis=0), axis=sumax), dtype=np.float32) * Atb(
                adddim(W[:,:,angle_index[j]], dim_exp) * (adddim(proj[:,:,angle_index[j]], dim_exp)
                                     - Ax(res, geo, angle, 'ray-voxel')),
                geo, angle, 'FDK')
            if noneg:
                res = res.clip(min=0)

            # VERBOSE:
            # proj_err = proj[angle_index[j]] - Ax(res, geo, angle_blocks[j],'ray-voxel')
            # weighted_err = W[angle_index[j]]*proj_err
            # backprj = Atb(weighted_err,geo,angle_blocks[j],'FDK')
            # weighted_backprj = 1/V[angle_index[j]]*backprj
            # res+=1*weighted_backprj
            # res[res < 0] = 0

            if Quameasopts != None:
                lq.append(MQ(res, res_prev, Quameasopts))

            res_prev = res
            tic = time.clock()
    lmbda *= lmbda_red
    # parkerweight(projsirt,TIGRE_parameters,angles,q=1)
    m = {
        'py_w': W,
        'py_v':V,
        'py_res':res

    }
    scipy.io.savemat('Tests/FDK_data', m)
    if Quameasopts != None:
        return res.transpose(), lq
    else:
        return res.transpose()
def adddim(array,dimexp):
    # This function makes sure the dimensions of the arrays are only expanded if
    # blocksize ==1. There may be a nicer way of doing this!
    if dimexp==True:
        return np.expand_dims(array,axis=2)
    else:
        return array