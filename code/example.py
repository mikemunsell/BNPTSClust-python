
# coding: utf-8

# In[1]:

# This notebook provides an example of using the python implementation of the BNPTSClust R package
# Code currently includes monthly time series clustering only (tseriescm)
# Original R code created by David Alejandro Martell Juarez
# Python implementation by Mike Munsell, Brandeis University

##### Import Required packages
import os
import pandas as pd
from tseriescm import tseriescm

##### Max display in order to plot of figures in the example notebook
pd.options.display.max_rows = 1000

##### Working directory to read in data
working_dir = os.getcwd()
data_path = os.path.join(working_dir,"..","data/stocks.csv")


# In[2]:

#### Read in stock data
stocks = pd.read_csv(data_path, index_col = 0)

##### Input data must be a pandas dataframe with the date as the row index,
##### and the individual time series as each column
stocks.head()


# In[4]:

##### Algorithm structure and default values are as follows. 
##### See code documentation for exact definitions of each function argument:
##### tseriescm(data, maxiter=400, burnin=(0.1*maxiter), thinning=5, 
#####          level=False, trend=True, seasonality=True, deg=2,
#####          c0eps=2, c1eps=1, c0beta=2, c1beta=1, c0alpha=2, c1alpha=1,
#####          priora=False, pia=0.5, q0a=1, q1a=1, priorb=False, q0b=1, q1b=1, a=0.25, b=0, indlpml=False, **kwargs)

tseriescm(stocks, maxiter = 500, priora=True, a=0.5, b=1)

# Iteration Number:  50 Progress:  10.0 % 

# Iteration Number:  100 Progress:  20.0 % 

# Iteration Number:  150 Progress:  30.0 % 

# Iteration Number:  200 Progress:  40.0 % 

# Iteration Number:  250 Progress:  50.0 % 

# Iteration Number:  300 Progress:  60.0 % 

# Iteration Number:  350 Progress:  70.0 % 

# Iteration Number:  400 Progress:  80.0 % 

# Iteration Number:  450 Progress:  90.0 % 

# Iteration Number:  500 Progress:  100.0 % 

# Number of groups of the chosen cluster configuration:  12
# Time series in group  0 [ 0  1  6  9 24 30 43] 

# Time series in group  1 [ 2  5  7  8 10 13 16 17 19 25 26 27 31 34 36 38 52 55] 

# Time series in group  2 [ 3  4 21 37] 

# Time series in group  3 [11 12 18 41 56 57] 

# Time series in group  4 [14 35 50] 

# Time series in group  5 [15 22 29 54] 

# Time series in group  6 [20 32 33 39 40 42 45 46 47 48 51] 

# Time series in group  7 [23] 

# Time series in group  8 [28] 

# Time series in group  9 [44] 

# Time series in group  10 [49] 

# Time series in group  11 [53] 

# HM Measure:  197.784711001