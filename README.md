#BNPTSClust monthly algorithm for python (working version)

Python implementation of function that performs the time series clustering algorithm 
described in Nieto-Barajas and Contreras-Cristan (2014) "A Bayesian Non-Parametric 
Approach for Time Series Clustering". Bayesian Analysis, Vol. 9, No. 1 (2014) pp.147-170".
This function is based on the BNPTSClust package for R, written by David Alejandro Martell
Juarez. This is a python implementation of the monthly time series function only - more
granular frequencies (weekly, daily) to come soon.

The majority of the documentation and variable/function names are modeled directly
from the R BNPTClust package in order to maintain consistency between languages. A Jupyter
notebook with an example using the monthly stock dataset from the R package is provided.

Link to [Nieto-Barajas and Contreras-Cristan (2014)](https://projecteuclid.org/download/pdfview_1/euclid.ba/1393251774). 

+   Author: Michael Munsell
+   Date: September 21, 2018
+   Code: Python 3.6.1, pandas, numpy, scipy