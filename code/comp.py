import numpy as np
import pandas as pd

def comp(vector):

  # Function that computes the distinct observations in a numeric vector.
  # It is based entirely on the "comp11" function from the BNPTSclust  
  # package in R created by David Alejandro Martell Juarez
  # 
  # IN:
  # 
  # vector <- numeric vector. 
  # 
  # OUT: 
  # 
  # jstar <- variable that rearranges the input vector into a vector with only 
  #          its unique values. 
  # nstar <- frequency of each distinct observation in the input vector. 
  # rstar <- number of distinct observations in the input vector.
  # gn    <- variable that indicates the group number to which every
  #          entry in the input vector belongs. 

    n = len(vector)

    mat = vector[:, None] == vector

    jstar = np.repeat(False, n)

    led = np.repeat(False, n)

    for j in np.arange(0,n):
        if not led[j]:
            jstar[j] = True
            if j+1 == n:
                break
            ji = np.arange(j+1, n)
            tt = mat[ji, j] == True
            led[ji] = led[ji] | tt
        if all(np.delete(led, np.arange(0,j+1))):
            break

    ystar = vector[jstar]
    nstar = np.apply_along_axis(np.sum, 0, mat[:, jstar])
    rstar = len(nstar)
    gn = pd.match(vector,ystar)
    
    return jstar, nstar, rstar, gn