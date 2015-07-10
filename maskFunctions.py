from __future__ import division
import numpy as np
import scipy.stats as stat
import scipy.ndimage as img
import growRegion
import scipy.misc as m
import os
from getmidpointcircle import getmidpointcircle

def circleMask(Image_dimensions, center, radius):
    H = Image_dimensions[0]
    W = Image_dimensions[1]
    CMinv = np.ones([H,W],dtype = np.bool)
    [X,Y] = getmidpointcircle(H/2,W/2,radius); # generate circle for circleMask
    for (x,y) in zip(X,Y):
        CMinv[x,y] = 0 # add perimeter of circle to mask
    (L,_) = img.measurements.label(CMinv) #label connected regions
    fill_region = L[center[1],center[0]] # find region containing center of circle
    CMinv[L == fill_region] = 0
    return ~CMinv

def lightMask(I,circleMask):
    [H,W] = I.shape
    I_vector = I.reshape([H*W])
    strongThresh = stat.scoreatpercentile(I_vector,99.5)
    weakThresh = stat.scoreatpercentile(I_vector,80)
    maskSeeds = I >= strongThresh # pick the seeds for the intensity mask
    seeds = np.where(maskSeeds)  # build a list of the seeds
    intensityMask = growRegion.growRegions(I,seeds,[weakThresh,255]) # find additional points derived from those seeds
    fullMask = np.logical_and(intensityMask , circleMask) # only pixels present in both masks make it to the filtered image
    return fullMask

def darkMask(I,circleMask):
    I2 = 255-I
    I2[~circleMask] = 0
    return lightMask(I2,circleMask)

def mask_generator(files):
    count = 0
    for infile in files:
        I_name = (os.path.splitext(os.path.basename(infile)))[0]
        yield m.imread(infile),I_name

def andMaskGenerator(maskGenerator, combineSize):
    count = 0
    for I2,I_name in maskGenerator:
        count += 1
        if count == 1:
            I = I2
        elif count == combineSize:
            I = np.logical_and(I,I2)
            yield I,I_name
            count = 0
        else:
            I = np.logical_and(I,I2)



def gridCells(mask):#takes a mask of dimension 4096x4096 and converts it to a 64x64 mask
        I = mask
        I = np.reshape(I,[64,262144],order = 'F');
        I = np.sum(I,axis = 0);
        I = np.reshape(I,[64,64,64],order = 'F');
        I = np.sum(I,axis = 1);
        I = np.reshape(I,[64,64],order = 'F');
        gridCells = I>0;
        return gridCells

def gridCellsDynamic(mask): #takes a mask of dimension N(64x64) and converts it to a 64x64 mask
        I = mask
        dim = I.shape[0]
        N = I.shape[0]/64
        I = np.reshape(I,[N,dim**2/N],order = 'F');
        I = np.sum(I,axis = 0);
        I = np.reshape(I,[64,N,64],order = 'F');
        I = np.sum(I,axis = 1);
        I = np.reshape(I,[64,64],order = 'F');
        gridCells = I>0;
        return gridCells
