import numpy as np

def scaleandperiods(df):

    # Function that receives a pandas data frame with the time series data and 
    # scales it in the [0,1] interval, as specified in the original paper.
    # The function considers that the time periods of the data appear 
    # as row names, and data series are columns .
    # 
    # IN:
    #
    # data <- pandas data frame with the time series information.
    #
    # OUT:
    # 
    # periods <- array with the time periods of the data. 
    # mydata  <- matrix with the time series data. 
    # cts     <- variable that indicates if some time series were removed
    #            because they were constant in time. If no time series were
    #            removed, cts = 0. If there were time series removed, cts
    #            indicates the column of such time series. 

    n = len(df)
    m = len(df.columns)
    periods = list(df.index)
    mydata = df
    
    maxima = np.zeros((m,1))
    minima = np.zeros((m,1))
    
    for i in range(0,m):
        maxima[i,0] = max(mydata.iloc[:,i])
        minima[i,0] = min(mydata.iloc[:,i])
    
    cts = np.where(maxima==minima)[0]
    
    if len(cts) > 0:
        mydata = mydata.drop(index = cts, inplace=True)
        n = len(mydata)
        m = len(mydata.columns)
        maxima = np.zeros((m,1))
        minima = np.zeros((m,1))
        
        for i in range(0,m):
            maxima[i,0] = max(mydata.iloc[:,i])
            minima[i,0] = min(mydata.iloc[:,i])
            
    for j in range(0,m):
        m1 = maxima[j,0] - minima[j,0]
        
        for k in range(0,n):
            mydata.iloc[k,j] = 1 + (1/m1)*(mydata.iloc[k,j] - maxima[j,0])
    
    return periods, mydata.as_matrix(), cts