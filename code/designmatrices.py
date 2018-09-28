import numpy as np
import math

def designmatrices(level,trend,seasonality,deg,T):

    # Function that generates the design matrices of the clustering
    # algorithm based on the parameters that the user wants to consider,
    # i.e. level, polinomial trend and/or seasonal components. It also 
    # returns the number of parameters that are considered and not
    # considered for clustering. Since this function is for internal use,
    # its arguments are taken directly from the clustering functions.
    # Currently, the function is only designed to handle monthly data.
    #
    # IN:
    #
    # level       <- Variable that indicates if the level of the time 
    #                series will be considered for clustering. If 
    #                level = 0, then it is omitted. If level = 1, then it 
    #                is taken into account.
    # trend       <- Variable that indicates if the polinomial trend of 
    #                the model will be considered for clustering. If 
    #                trend = 0, then it is omitted. If trend = 1, then it
    #                is taken into account.
    # seasonality <- Variable that indicates if the seasonal components 
    #                of the model will be considered for clustering. 
    #                If seasonality = 0, then they are omitted. If 
    #                seasonality = 1, then they are taken into account.
    # deg         <- Degree of the polinomial trend of the model.
    # T           <- Number of periods of the time series.
    #
    # OUT:
    #
    # Z <- Design matrix of the parameters not considered for clustering.
    # X <- Design matrix of the parameters considered for clustering.
    # p <- Number of parameters not considered for clustering.
    # d <- Number of parameters considered for clustering.


    M = np.zeros((T,1+deg+11))
    M[:,0] = 1
    for i in range(1,deg+1): 
        M[:,i] = np.arange(1,T+1)**i
        
    num = math.floor(T/12)
    
    if num < 1:
        X2 = np.eye(T-1)
        X2 = np.concatenate((X2,np.zeros((T-1,1))), axis=1) #Add zero column
        X <- np.concatenate((X2,np.zeros((1,T))), axis = 0) #Add zero row
    else:

    # Matrix that contains the indicator functions for the 11 months and one row of zeros to avoid singularity problems in the design matrix 
    
        X21 = np.concatenate((np.eye(11), np.zeros((1,11))))
        X2 = X21
        resid = T % 12
        
        if num >= 2:
            for i in range(2,num+1):
                X2 = np.concatenate((X2,X21))

    M[:,(deg+1):(1+deg+11)] = np.concatenate((X2,X21[0:resid]))
    
    if (level == 0) & (trend == 0) & (seasonality == 0):
        p = 1+deg+11
        d = 0
        Z = M
        X = 0
        
    elif (level == 0) & (trend == 0) & (seasonality == 1):
        p = 1+deg
        d = 11
        Z = M[:,0:(deg+1)]
        X = M[:, (deg+1):(1+deg+11)]
        
    elif (level == 0) & (trend == 1) & (seasonality == 0):
        p = 1+11
        d = deg
        Z = np.concatenate((M[:,0].reshape(T,1),M[:,(deg+1):(1+deg+11)]),axis=1)
        X = M[:,1:(deg+1)]
    
    elif (level == 1) & (trend == 0) & (seasonality == 0):
        p = deg+11
        d = 1
        Z = M[:,1:(1+deg+11)]
        X = M[:,0].reshape(T,1)
        
    elif (level == 1) & (trend == 1) & (seasonality == 0):
        p = 11
        d = 1+deg
        Z = M[:,(deg+1):(1+deg+11)]
        X = M[:,0:(deg+1)]
        
    elif (level == 1) & (trend == 0) & (seasonality == 1):
        p = deg
        d = 1+11
        Z = M[:, 1:(deg+1)]
        X = np.concatenate((M[:,0].reshape(T,1),M[:,(deg+1):(1+deg+11)]),axis=1)
    
    elif (level == 0) & (trend == 1) & (seasonality == 1):
        p = 1
        d = deg+11
        Z = M[:,0].reshape(T,1)
        X = M[:,1:(1+deg+11)]
    
    elif (level == 1) & (trend == 1) & (seasonality == 1):
        p = 0
        d = 1+deg+11
        X = M
        Z = 0
    
    return(p,d,X,Z)