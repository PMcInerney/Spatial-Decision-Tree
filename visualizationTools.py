from __future__ import division
import numpy as np

def drawSquare(image,cellr,cellc,color): # this draws a square on a solar thumbnail
  color = np.array(color)
  color = color.reshape([1,1,3])
  I = image
  L = 4*cellc
  R = L+3
  U = 4*cellr
  D = U+3
  if I.ndim == 2: # if the image is greyscale, expand it to RGB
    I = np.expand_dims(I,2)
    I = np.concatenate((I,I,I),axis = 2)
  for i in range(4):
    I[U,L+i,:] = color
    I[D,L+i,:] = color
    I[U+i,L,:] = color
    I[U+i,R,:] = color
  return I

def dispTree(tree,imageFile):
  raise Exception('Not Implemented')

