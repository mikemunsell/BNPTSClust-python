import numpy as np
import scipy
import math
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style="whitegrid")
from scipy.stats import multivariate_normal
from scipy.linalg import inv
from comp import comp
from scaleandperiods import scaleandperiods
from designmatrices import designmatrices

# Function that performs the time series clustering algorithm
# described in Nieto-Barajas and Contreras-Cristan (2014) "A Bayesian
# Non-Parametric Approach for Time Series Clustering". Bayesian 
# Analysis, Vol. 9, No. 1 (2014) pp.147-170". This function is based on 
# the BNPTSClust package for R, written by David Alejandro Martell Juarez.
# This is a python implementation of the monthly time series function.
# The majority of the code documentation, comments, and variable/function names are 
# pulled directly from the R BNPTClust package for consistency between languages. 
#
# IN:
#
# data    <- Pandas data frame with the time series information. 
# maxiter <- Maximum number of iterations for Gibbs sampling.
#            Default value = 1000.
# burnin  <- Burn-in period of the Markov Chain generated by Gibbs
#            sampling. 
# thinning <- Number that indicates how many Gibbs sampling simulations
#             should be skipped to form the Markov Chain.
# level   <- Flag that indicates if the level of the time 
#            series will be considered for clustering. If TRUE, then it 
#            is taken into account.
# trend   <- Flag that indicates if the polinomial trend of 
#            the model will be considered for clustering. 
#            If TRUE, then it is taken into account. 
# seasonality <- Flag that indicates if the seasonal components 
#                of the model will be considered for clustering. 
#                If TRUE, then they are taken into account.
# deg     <- Degree of the polinomial tendency of the model. 
#            Default value = 2. 
# c0eps   <- Shape parameter of the hyper-prior distribution 
#            on sig2eps. Default value = 2.
# c1eps   <- Rate parameter of the hyper-prior distribution 
#            on sig2eps. Default value = 1.
# c0beta  <- Shape parameter of the hyper-prior distribution 
#            on sig2beta. Default value = 2.
# c1beta  <- Rate parameter of the hyper-prior distribution 
#            on sig2beta. Default value = 1.
# c0alpha <- Shape parameter of the hyper-prior distribution 
#            on sig2alpha. Default value = 2.
# c1alpha <- Rate parameter of the hyper-prior distribution 
#            on sig2alpha. Default value = 1.
# priora  <- Flag that indicates if a prior on parameter "a" is
#            to be assigned. If TRUE, a prior on "a" is assigned.
#            Default value = FALSE.
# pia     <- Mixing proportion of the prior distribution on parameter 
#            "a". Default value = 0.5.
# q0a     <- Shape parameter of the continuous part of the prior
#            distribution on parameter "a". Default value = 1.
# q1a     <- Shape parameter of the continuous part of the prior
#            distribution on parameter "a". Default value = 1.
# priorb  <- Flag that indicates if a prior on parameter "b" is
#            to be assigned. If TRUE, a prior on "b" is assigned.
#            Default value = FALSE.
# q0b     <- Shape parameter of the prior distribution on parameter 
#            "b". Default value = 1.
# q1b     <- Shape parameter of the prior distribution on parameter 
#            "b". Default value = 1.
# a       <- Initial/fixed value of parameter "a". 
#            Default value = 0.25.
# b       <- Initial/fixed value of parameter "b". 
#            Default value = 0.
# indlpml <- Flag that indicates if the LPML is to be calculated.
#            If TRUE, LPML is calculated. Default value = FALSE.
# 
# OUT:
#
# Running this function results in the following printed ouput:
#     1) The group number to which each column (time series) of the input 
#        matrix belongs to after clustering
#     2) The Heterogeneity Measure of the final cluster configuration
#     3) Graphical representations of the final cluster configuration
#        (One plot for each cluster)

sentinel = object()

def tseriescm(data, maxiter=400, burnin=sentinel, thinning=5, 
              level=False, trend=True, seasonality=True, deg=2,
              c0eps=2, c1eps=1, c0beta=2, c1beta=1, c0alpha=2, c1alpha=1,
              priora=False, pia=0.5, q0a=1, q1a=1, priorb=False, q0b=1, q1b=1, a=0.25, b=0, indlpml=False, **kwargs):
    
    if burnin == sentinel:
        burnin = math.floor(0.1*maxiter)
    
    if deg%1 !=0 or deg <= 0:
        raise ValueError("deg must be a positive integer number.")
        
    if maxiter%1 != 0 or maxiter <= 0:
        raise ValueError("maxiter must be a positive (large) integer number.")
        
    if burnin%1 != 0 or burnin <= 0:
        raise ValueError("burnin must be a non-negative integer number.")
        
    if thinning%1 != 0 or thinning <= 0:
        raise ValueError("thinning must be a non-negative integer number.")
        
    if maxiter <= burnin:
        raise ValueError("maxiter cannot be less than or equal to burnin.")
    
    if c0eps <= 0 or c1eps <= 0 or c0beta <= 0 or c1beta <= 0 or c0alpha <= 0 or c1alpha <= 0:
        raise ValueError("c0eps,c1eps,c0beta,c1beta,c0alpha and c1alpha must be positive numbers.")
    
    if pia <= 0 or pia >= 1:
        raise ValueError("The mixing proportion pia must be a number in (0,1).")
    
    if q0a <= 0 or q1a <= 0:
        raise ValueError("q0a and q1a must be positive numbers.")
    
    if a < 0 or a >= 1:
        raise ValueError("'a' must be a number in [0,1).")
    
    if q0b <= 0 or q1b <= 0:
        raise ValueError("q0b and q1b must be positive numbers.")
    
    if b <= -a:
        raise ValueError("'b' must be greater than '-a'.")
        
    periods, mydata, cts = scaleandperiods(data) 		
    
    ##### Construction of the design matrices#####
    T = mydata.shape[0]					# Number of periods of the time series
    n = mydata.shape[1]                 # Number of time series present in the data
    p,d,X,Z = designmatrices(level,trend,seasonality,deg,T)
   
	##### Initial Values for the parameters that will be part of the gibbs sampling #####   
    sig2eps = np.ones(n) 				# Vector that has the diagonal entries of the variance-covariance matrix for every epsilon_i.
    sig2the = 1              			# Initial value for sig2the.
    rho = 0                  			# Initial value for rho. 
    
    P = np.zeros((T,T))      			# Initial matrix P.                        

    for j in np.arange(1,T+1):
        for k in np.arange(1,T+1):
            P[j-1,k-1] = rho**(abs(j-k))
            

    R = sig2the*P                 		# Initial matrix R.
    
    if level + trend + seasonality == 0:
        sig2alpha = np.ones(p) 			# Vector that has the diagonal entries of the variance-covariance matrix for alpha.
        sigmaalpha = np.diag(sig2alpha) # Variance-covariance matrix for alpha.
        invsigmaalpha = np.diag(1/sig2alpha) # Inverse variance-covariance matrix for alpha.
    
        alpha = np.random.multivariate_normal(np.zeros(p), sigmaalpha, size = n).T # alpha is a matrix with a vector value of alpha for every time series in its columns. 
        theta = np.random.multivariate_normal(np.zeros(T), R, size = n).T  # theta is a matrix with a vector value of theta for every time series in its columns.        
        gamma = theta  # gamma is the union by rows of the beta and theta matrices 
        
    elif level + trend + seasonality == 3:
        sig2beta = np.ones(d)
        sigmabeta = np.diag(sig2beta)
        invsigmabeta = np.diag(1/sig2beta)
        
        beta = np.random.multivariate_normal(np.zeros(d), sigmabeta, size = n).T
        theta = np.random.multivariate_normal(np.zeros(T), R, size = n).T          
        gamma = np.concatenate((beta, theta))
    else:
        sig2beta = np.ones(d)
        sigmabeta = np.diag(sig2beta)
        invsigmabeta = np.diag(1/sig2beta)
        sig2alpha = np.ones(p) 
        sigmaalpha = np.diag(sig2alpha) 
        invsigmaalpha = np.diag(1/sig2alpha)
        
        alpha = np.random.multivariate_normal(np.zeros(p), sigmaalpha, size = n).T 
        beta = np.random.multivariate_normal(np.zeros(d), sigmabeta, size = n).T
        theta = np.random.multivariate_normal(np.zeros(T), R, size = n).T 
        gamma = np.concatenate((beta, theta))

    iter0 = 0                                    
    iter1 = 0               # Counter for the number of iterations saved during the Gibbs sampling.
    arrho = 0               # Variable that will contain the acceptance rate of rho in the Metropolis-Hastings step.
    ara = 0                 # Variable that will contain the acceptance rate of a in the Metropolis-Hastings step.
    arb = 0                 # Variable that will contain the acceptance rate of b in the Metropolis-Hastings step.
    sim = np.zeros((n,n))   # Initialization of the similarities matrix.

    if thinning == 0:
        CL = math.floor(maxiter-burnin)
    else:
        CL = math.floor((maxiter-burnin)/thinning)
        
    memory = np.zeros((CL*n,n))      # Matrix that will contain the cluster configuration of every iteration that is saved during the Gibbs sampling.
    memorygn = np.zeros((CL,n))      # Matrix that will save the group number to which each time series belongs in every iteration saved.  
    sig2epssample = np.zeros((CL,n)) # Matrix that in its columns will contain the sample of each sig2eps_i's posterior distribution after Gibbs sampling.
    sig2thesample = np.zeros((CL,1)) # Vector that will contain the sample of sig2the's posterior distribution after Gibbs sampling. 
    rhosample = np.zeros((CL,1))     # Vector that will contain the sample of rho's posterior distribution after Gibbs sampling.
    asample = np.zeros((CL,1))       # Vector that will contain the sample of a's posterior distribution after Gibbs sampling.
    bsample = np.zeros((CL,1))       # Vector that will contain the sample of b's posterior distribution after Gibbs sampling.
    msample = np.zeros((CL,1))       # Vector that will contain the sample of the number of groups at each Gibbs sampling iteration.

    if level + trend + seasonality == 0:
        sig2alphasample = np.zeros((CL,p)) # Matrix that in its columns will contain the sample of each sig2alpha_i's posterior distribution after Gibbs sampling.
    elif level + trend + seasonality == 3:
        sig2betasample = np.zeros((CL,d)) # Matrix that in its columns will contain the sample of each sig2beta_i's posterior distribution after Gibbs sampling.
    else:
        sig2alphasample = np.zeros((CL,p))
        sig2betasample = np.zeros((CL,d))
    
    if indlpml != 0:
        iter2 = 0
        auxlpml = np.zeros((math.floor((maxiter-burnin)/10),n))
        
##### BEGINNING OF GIBBS SAMPLING #####

    while iter0 < maxiter:

        ##### 1) SIMULATION OF ALPHA'S POSTERIOR DISTRIBUTION #####

        if level + trend + seasonality != 3:
            if level + trend + seasonality == 0:
                for i in range(0,n):
                    sigmaeps = np.diag(np.repeat(sig2eps[i],T))
                    Q = sigmaeps + R
                    Qinv = inv(Q)
                    Winv = Qinv
                    W = Q

                    Valphainv = (np.transpose(Z).dot(Winv).dot(Z))+invsigmaalpha
                    Valpha = inv(Valphainv)

                    mualpha = Valpha.dot(np.transpose(Z)).dot(Winv).dot(mydata[:,i])

                    alpha[:,i] = np.random.multivariate_normal(mualpha, Valpha, size = 1)
            else:
                for i in range(0,n):
                    sigmaeps = np.diag(np.repeat(sig2eps[i],T))
                    Q = sigmaeps + R
                    Qinv = inv(Q)
                    Vinv = (np.transpose(X).dot(Qinv).dot(X))+invsigmabeta
                    V = inv(Vinv)

                    Winv = Qinv + Qinv.dot(X).dot(V).dot(np.transpose(X)).dot(Qinv)
                    W = inv(Winv)

                    Valphainv = (np.transpose(Z).dot(Winv).dot(Z))+invsigmaalpha
                    Valpha = inv(Valphainv)

                    mualpha = Valpha.dot(np.transpose(Z)).dot(Winv).dot(mydata[:,i])

                    alpha[:,i] = np.random.multivariate_normal(mualpha, Valpha, size = 1)
                       

##### 2) SIMULATION OF GAMMA'S = (BETA,THETA) POSTERIOR DISTRIBUTION #####
        for i in range(0,n):
            jstar, nstar, mi, gn  = comp(np.delete(gamma[0,:], i))  # Only the first entries of gamma[,-i] are compared to determine the cluster configuration
            gmi = np.delete(gamma, i, axis=1)    
            gammastar = gmi[:, jstar]    							# Matrix with all the elements of gamma, except for the i-th element
            if level + trend + seasonality == 0:
                thetastar = gammastar[d:(T+d), :]
            else:
                if d == 1:
                    betastar = gammastar[0:d, :] 					# Separation of unique vectors between betastar and thetastar
                    thetastar = gammastar[d:(T+d), :]
                else:
                    betastar = gammastar[0:d, :]
                    thetastar = gammastar[d:(T+d),:]

            sigmaeps = sig2eps[i]*np.diag(np.repeat(1,T))
            invsigmaeps = (1/sig2eps[i])*np.diag(np.repeat(1,T))
            Q = sigmaeps + R
            Qinv = inv(Q)
            
            if level + trend + seasonality == 0:
                Winv = Winv
                W = Q
            else:
                Vinv = (np.transpose(X).dot(Qinv).dot(X))+invsigmabeta
                V = inv(Vinv)
                
                Winv = Qinv + (Qinv.dot(X).dot(V).dot(np.transpose(X)).dot(Qinv))
                W = inv(Winv)

        
        	# Computing weigths for gamma(i)'s posterior distribution
            if level + trend + seasonality == 0: 
                dj = np.zeros((mi))
                d0 = (b + a*mi)*multivariate_normal.pdf(mydata[:,i],(Z.dot(alpha[:,i])), W)
                
                den = 0
                
                for j in range(0,mi):
                    dj[j] <- (nstar[j] - a)*multivariate_normal.pdf(mydata[:,i],(Z.dot(alpha[:,i])+thetastar[:,j]), sigmaeps)
            
                den = d0 + sum(dj)
                if den == 0:
                    d0 = (b + a*mi) + multivariate_normal.logpdf(mydata[:,i],(Z.dot(alpha[:,i])),W)
                    for j in range(0,mi):
                        dj[j] = (nstar[j] - a) + multivariate_normal.logpdf(mydata[:,i], (Z.dot(alpha[:,i])+thetastar[:,j]), sigmaeps)
                    dj = np.concatenate((dj,d0))
                    aa = min(dj)
                    q = (1+(dj-aa)+(dj-aa)**2/2)/sum(1+(dj-aa)+(dj-aa)**2/2)
                else:
                    q = dj/den
                    q = np.append(q,(d0/den))
                
            elif level + trend + seasonality == 3:
                dj = np.zeros((mi))
                d0 = (b+a*mi)*multivariate_normal.pdf(mydata[:,i],np.zeros((T)),W)
                
                den = 0
                
                for j in range(0,mi):
                    dj[j] = (nstar[j] - a)*multivariate_normal.pdf(mydata[:,i],(X.dot(betastar[:,j])+thetastar[:,j]), sigmaeps)
                
                den = d0 + sum(dj)
                if den == 0:
                    d0 = (b + a*mi) + multivariate_normal.logpdf(mydata[:,i],np.zeros((T)),W)
                    for j in range(0,mi):
                        dj[j] = (nstar[j] - a) + multivariate_normal.logpdf(mydata[:,i], (X.dot(betastar[:,j])+thetastar[:,j]), sigmaeps)
                    dj = np.concatenate((dj,d0))
                    aa = min(dj)
                    q = (1+(dj-aa)+(dj-aa)**2/2)/sum(1+(dj-aa)+(dj-aa)**2/2)
                else:
                    q = dj/den
                    q = np.append(q,(d0/den))
                    
            else:
                dj = np.zeros((mi))
                d0 = (b+a*mi)*multivariate_normal.pdf(mydata[:,i],(Z.dot(alpha[:,i])),W)
                
                den = 0
                
                for j in range(0,mi):
                    dj[j] = (nstar[j] - a)*multivariate_normal.pdf(mydata[:,i], (Z.dot(alpha[:,i]) + X.dot(betastar[:,j])+thetastar[:,j]), sigmaeps)
                
                den = d0 + sum(dj)
                if den == 0:
                    d0 = (b + a*mi) + multivariate_normal.logpdf(mydata[:,i],Z*alpha[:,i],W)
                    for j in range(0,mi):
                        dj[j] = (nstar[j] - a) + multivariate_normal.logpdf(mydata[:,i], (Z.dot(alpha[:,i]) + X.dot(betastar[:,j]) + thetastar[:,j]), sigmaeps)
                    dj = np.concatenate(dj,d0)
                    aa = min(dj)
                    q = (1+(dj-aa)+(dj-aa)**2/2)/sum(1+(dj-aa)+(dj-aa)**2/2)
                else: 
                    q = dj/den
                    q = np.append(q,(d0/den))
 
    		# Sampling a number between 1 and (mi+1) to determine what will be the simulated value for gamma(i)
    		# The probabilities of the sample are based on the weights previously computed
            y = np.random.choice(np.arange(1,(mi+2)), size=1, replace=False, p=q)
        
    		# If sample returns the value (mi+1), a new vector from g0 will be simulated and assigned to gamma(i)
            if y == (mi+1):
                if level+trend+seasonality == 0:
                    Sthetai = inv(invsigmaeps+inv(R))
                    muthetai = Sthetai.dot(invsigmaeps).dot(mydata[:,i]-(Z.dot(alpha[:,i])))
                    theta0 = np.random.multivariate_normal(muthetai, Sthetai)
                    gamma[:,i] = theta0
                elif level+trend+seasonality == 3:
                    Sthetai = inv(invsigmaeps+inv(R))
                    muthetai = Sthetai.dot(invsigmaeps).dot(mydata[:,i]-(X.dot(beta[:,i])))
                    mubetai = V.dot(np.transpose(X)).dot(Qinv).dot(mydata[:,i])
                    beta0 = np.random.multivariate_normal(mubetai,V)
                    theta0 = np.random.multivariate_normal(muthetai,Sthetai)
                    gamma[:,i] = np.concatenate((beta0, theta0))
                else:
                    Sthetai = inv(invsigmaeps + inv(R))
                    muthetai = Sthetai.dot(invsigmaeps).dot(mydata[:,i] - (Z.dot(alpha[:,i])) - (X.dot(beta[:,i])))
                    mubetai = V.dot(np.transpose(X)).dot(Qinv).dot(mydata[:,i] - (Z.dot(alpha[:,i])))
                    beta0 = np.random.multivariate_normal(mubetai,V)
                    theta0 = np.random.multivariate_normal(muthetai,Sthetai)
                    gamma[:,i] = np.concatenate((beta0,theta0))
            else:
                gamma[:,i] = gammastar[:,y-1].reshape(len(gammastar))    # Otherwise, column y from gammastar will be assigned to gamma(i)

        ##### 2.1) ACCELERATION STEP AND CONSTRUCTION OF SIMILARITIES MATRIX #####
        jstar, nstar, m, gn = comp(gamma[0,:])
        gammastar = gamma[:,jstar]
        
        if level + trend + seasonality == 0:
            theta = (gamma[d:(T+d),:])
            thetastar = gammastar[d:(T+d),:]
        else:
            if d==1:
                beta = gamma[0:d,:]
                theta = gamma[d:(T+d),:]
                betastar = gammastar[0:d,:]
                thetastar = gammastar[d:(T+d),:]
            else:
                beta = gamma[0:d,:]
                theta = gamma[d:(T+d),:]
                betastar = gammastar[0:d,:]
                thetastar = gammastar[d:(T+d),:]
                
        for j in range(0,m):
            
            if level + trend + seasonality == 0:
                cc = np.where(gn == j)  	# Identifying the cluster configuration of each group.
                aux = np.zeros((T,T))       # Calculating the necessary matrices for the simulation of the distributions for the acceleration step.
                aux1 = np.zeros((T,1))
                aux2 = np.zeros((T,1))
                
                for i in range(0,nstar[j]):
                    aux = aux + np.diag(np.repeat(1/sig2eps[cc[0][i]],T))
                    aux1 = aux1 + (np.diag(np.repeat(1/sig2eps[cc[0][i]],T)).dot(mydata[:,i]-Z.dot(alpha[:,i]))).reshape((T,1))
                    
                Sthetastar = inv(aux+inv(R))
                muthetastar = Sthetastar.dot(aux1)
                
                theta[:,cc[0]] = np.random.multivariate_normal(muthetastar.flatten(),Sthetastar).reshape((len(muthetastar),1))
                
            elif level + trend + seasonality == 3:
                cc = np.where(gn == j)      
                aux = np.zeros((T,T))       
                aux1 = np.zeros((T,1))
                aux2 = np.zeros((T,1))
                
                for i in range(0,nstar[j]):
                    aux = aux + np.diag(np.repeat(1/sig2eps[cc[0][i]],T))
                    aux1 = aux1 + (np.diag(np.repeat(1/sig2eps[cc[0][i]],T)).dot(mydata[:,i]-X.dot(betastar[:,j]))).reshape((T,1))
                    aux2 = aux2 + (np.diag(np.repeat(1/sig2eps[cc[0][i]],T)).dot(mydata[:,i]-thetastar[:,j])).reshape((T,1))
                
                Sthetastar = inv(aux + inv(R))
                muthetastar = Sthetastar.dot(aux1)
                Sbetastar = inv(np.transpose(X).dot(aux).dot(X) + invsigmabeta)
                mubetastar = Sbetastar.dot(np.transpose(X)).dot(aux2)
                
                beta[:,cc[0]] = np.random.multivariate_normal(mubetastar.flatten(),Sbetastar).reshape((len(mubetastar),1))
                theta[:,cc[0]] = np.random.multivariate_normal(muthetastar.flatten(),Sthetastar).reshape((len(muthetastar),1))
                
            else:
                cc = np.where(gn == j)      
                aux = np.zeros((T,T))       
                aux1 = np.zeros((T,1))
                aux2 = np.zeros((T,1))
                
                for i in range(0,nstar[j]):
                    aux = aux + np.diag(np.repeat(1/sig2eps[cc[0][i]],T))
                    aux1 = aux1 + (np.diag(np.repeat(1/sig2eps[cc[0][i]],T)).dot(mydata[:,i]-Z.dot(alpha[:,i])-X.dot(betastar[:,j]))).reshape((T,1))
                    aux2 = aux2 + (np.diag(np.repeat(1/sig2eps[cc[0][i]],T)).dot(mydata[:,i]-Z.dot(alpha[:,i])-thetastar[:,j])).reshape((T,1))
                    
                Sthetastar = inv(aux + inv(R))
                muthetastar = Sthetastar.dot(aux1)
                Sbetastar = inv(np.transpose(X).dot(aux).dot(X) + invsigmabeta)
                mubetastar = Sbetastar.dot(np.transpose(X)).dot(aux2)
                
                beta[:,cc[0]] = np.random.multivariate_normal(mubetastar.flatten(),Sbetastar).reshape((len(mubetastar),1))
                theta[:,cc[0]] = np.random.multivariate_normal(muthetastar.flatten(),Sthetastar).reshape((len(muthetastar),1))
                
            if (iter0 % thinning == 0) & iter0 >= burnin:
                for i1 in range(0,nstar[j]):
                    for i2 in range(i1,nstar[j]):
                        sim[cc[0][i1],cc[0][i2]] = sim[cc[0][i1],cc[0][i2]] + 1
                        sim[cc[0][i2],cc[0][i1]] = sim[cc[0][i2],cc[0][i1]] + 1
                        memory[cc[0][i1] + (n*iter1), cc[0][i2]] = memory[cc[0][i1] + (n*iter1), cc[0][i2]] + 1
                        memory[cc[0][i2] + (n*iter1), cc[0][i1]] = memory[cc[0][i2] + (n*iter1), cc[0][i1]] + 1

        if level+trend+seasonality == 0:
            gamma = theta
        else:
            gamma = np.concatenate((beta, theta), axis=0)    # Obtaining all gamma vectors after the acceleration step.
            
        jstar, nstar, m, gn = comp(gamma[1,:])
        gammastar = gamma[:, jstar]
        
        if level+trend+seasonality == 0: 
            theta = gamma[d:(T+d),:]
            thetastar = gammastar[d:(T+d),:]
        else:
            if d==1:
                beta = gamma[0:d,:]
                theta = gamma[d:(T+d),:]
                betastar = gammastar[0:d,:]
                thetastar = gammastar[d:(T+d),:]
            else:
                beta = gamma[0:d,:]
                theta = gamma[d:(T+d),:]
                betastar = gammastar[0:d,:]
                thetastar = gammastar[d:(T+d),:]
                
##### 3) SIMULATION OF SIG2EPS' POSTERIOR DISTRIBUTION #####
        if level+trend+seasonality == 0:
            M = np.transpose(mydata - Z.dot(alpha) - theta).dot(mydata - Z.dot(alpha) - theta)
        elif level+trend+seasonality == 3:
            M = np.transpose(mydata - X.dot(beta) - theta).dot(mydata - X.dot(beta) - theta)
        else:
            M = np.transpose(mydata - Z.dot(alpha)-X.dot(beta) - theta).dot(mydata - Z.dot(alpha) - X.dot(beta) - theta)

        sig2eps = scipy.stats.invgamma.rvs((c0eps + T/2), scale = (c1eps + M.diagonal()/2), size = n)

##### 4) SIMULATION OF SIMGAALPHA'S POSTERIOR DISTRIBUTION #####
        if level+trend+seasonality != 3:
            sig2alpha = scipy.stats.invgamma.rvs((c0alpha + n/2), scale = (c1alpha + (alpha**2).sum(axis=1)), size = p)
            sigmaalpha = np.diag(sig2alpha)     
            invsigmaalpha = np.diag(1/sig2alpha)       

##### 5) SIMULATION OF SIGMABETA'S POSTERIOR DISTRIBUTION #####
        if level+trend+seasonality != 0:
            diff_in_shape = d-betastar.shape[1]
            if diff_in_shape < 0:
                sig2beta = 1/scipy.stats.invgamma.rvs((c0beta + m/2), scale = (c1beta + ((betastar**2).sum(axis=0)/2)))[0:d]
            elif diff_in_shape <= (betastar.shape[1]/2):
                sig2beta = 1/np.concatenate((scipy.stats.invgamma.rvs((c0beta + m/2), scale = (c1beta + ((betastar**2).sum(axis=0)/2)), size = betastar.shape[1]),\
                                 scipy.stats.invgamma.rvs((c0beta + m/2), scale = (c1beta + ((betastar**2).sum(axis=0)/2)), size = betastar.shape[1])[:diff_in_shape]))
            else:
                beta_vector = []
                for v in range(0,(math.floor(d/betastar.shape[1]))):
                    beta_vector = np.concatenate((beta_vector, scipy.stats.invgamma.rvs((c0beta + m/2), scale = (c1beta + ((betastar**2).sum(axis=0)/2)), size = betastar.shape[1])))
                sig2beta = 1/np.concatenate((beta_vector,scipy.stats.invgamma.rvs((c0beta + m/2), scale = (c1beta + ((betastar**2).sum(axis=0)/2)), size = betastar.shape[1])[:(d % betastar.shape[1])]))
            
            sigmabeta = np.diag(sig2beta)
            invsigmabeta = np.diag(1/sig2beta)

##### 6) SIMULATION OF SIG2THE'S POSTERIOR DISTRIBUTION #####
        cholP = np.linalg.cholesky(P) 
        Pinv = inv(cholP)             
        s1 = 0

        # Calculating the sum necessary for the rate parameter of the posterior distribution.
        for j in range(0,m):
            s1 = s1 + np.transpose(thetastar[:,j]).dot(Pinv).dot(thetastar[:,j])
            if s1 < 0:
            	s1 = s1*-1
        sig2the = scipy.stats.invgamma.rvs((m*T/2), scale = (s1/2), size = 1)

##### 7) SIMULATION OF RHO'S POSTERIOR DISTRIBUTION (Metropolis-Hastings step) #####
        rhomh = np.random.uniform(low=-1, high=1, size=1) 
        Pmh = np.zeros((T,T)) 
        
        # Calculating the matrix P for the proposed value rhomh.
        for j in range(1,T+1):
            for k in range(1,T+1):
                Pmh[j-1,k-1] = rhomh**(abs(j-k))

        cholPmh = scipy.linalg.cholesky(Pmh)
        Pmhinv = inv(cholPmh)                
        s = 0

        # Calculating the sum necessary for the computation of the acceptance probability.
        for j in range(0,m):
            s = np.add(s,np.asmatrix(thetastar[:,j]).dot(Pmhinv-Pmh).dot(np.transpose(np.asmatrix(thetastar[:,j])))) 

        # Computation of the acceptance probability.
        q = (-m)*(np.log(np.prod(np.diag(cholPmh))) - np.log(np.prod(np.diag(cholP)))) - ((1/(2*sig2the))*s) + (1/2)*(np.log(1+ rhomh*rhomh) - np.log(1+ rho*rho)) - np.log(1-rhomh*rhomh) + np.log(1- rho*rho)

        # Definition of the acceptance probability. 
        quot = min(0,q)

        # Sampling a uniform random variable in [0,1] to determine if the proposal is accepted or not.
        unif1 = np.random.uniform(low=0, high=1, size=1)

        # Acceptance step.
        if np.log(unif1) <= quot:
            rho = rhomh
            arrho = arrho + 1

            for j in np.arange(1,T+1):
                for k in np.arange(1,T+1):
                    P[j-1,k-1] = rho**(abs(j-k))

        R = sig2the*P 

##### 8) SIMULATION OF A'S POSTERIOR DISTRIBUTION (METROPOLIS-HASTINGS WITH UNIFORM PROPOSALS) #####
        if priora == 1:
            if b < 0:
                amh = np.random.uniform(low=-b, high=1, size=1)
            else:
                unif2 = np.random.uniform(low=0, high=1, size=1)
                if unif2 <= 0.5:
                    amh = 0
                else:
                    amh = np.random.uniform(low=0, high=1, size=1)

            # If b is not greater than -a, then accept the proposal directly.    
            if a+b <= 0:
                a = amh
                print("a + b < 0")
            else:
                quot1 = 0

                if(m > 1):
                    for j in range(0,m-1):
                        quot1 = quot1 + np.log(b + (j+1)*amh) + np.log(scipy.special.gamma(nstar[j] - amh)) - np.log(scipy.special.gamma(1-amh)) - np.log(b + (j+1)*a) - np.log(scipy.special.gamma(nstar[j]-a)) + np.log(scipy.special.gamma(1-a))

                quot1 = quot1 + np.log(scipy.special.gamma(nstar[m-1]-amh)) - np.log(scipy.special.gamma(1-amh)) - np.log(scipy.special.gamma(nstar[m-1] - a)) + np.log(scipy.special.gamma(1-a))

                if a == 0:
                    fa = 0.5
                else:
                    fa = 0.5*scipy.stats.beta.pdf(a, q0a, q1a)

                if amh == 0:
                    famh = 0.5
                else:
                    famh = 0.5*scipy.stats.beta.pdf(amh, q0a, q1a)

                # Quotient to evaluate the Metropolis-Hastings step in logs 
                quot1 = quot1 + np.log(famh) - np.log(fa)

                # Determination of the probability for the Metropolis-Hastings step
                alphamh1 = min(quot1,0)

                unif3 = np.random.uniform(low=0, high=1, size=1)

                # Acceptance step
                if np.log(unif3) == alphamh1:
                    a = amh
                    ara = ara + 1 
                    
##### 9) SIMULATION OF B'S POSTERIOR DISTRIBUTION (METROPOLIS-HASTINGS WITH GAMMA PROPOSALS) #####
        if priorb == 1:
            y1 = scipy.stats.gamma.rvs(1,1, scale = 10)
            bmh = y1 - a

            # If b is not greater than -a, then accept the proposal directly.
            if a+b <= 0:
                b = bmh
                print("a+b < 0")
            else:
                quot2 = 0

                if m > 1:
                    for j in range(0,m-1):
                        quot2 = quot2 + np.log(bmh + (j+1)*a) - np.log(b + (j+1)*a)

                fb = scipy.stats.gamma.pdf(a+b,q0b,scale = q1b)
                fbmh = scipy.stats.gamma.pdf(y1, q0b, scale = q1b)

                # Quotient to evaluate the Metropolis-Hastings step in logs
                quot2 = quot2 + (np.log(scipy.special.gamma(bmh+1)) - np.log(scipy.special.gamma(bmh+n)) - np.log(scipy.special.gamma(b+1)) + np.log(scipy.special.gamma(b+n))) + (np.log(fbmh) - np.log(fb)) - 0.1*(b-bmh)

                # Determination of the probability for the Metropolis-Hastings step
                alphamh2 = min(quot2,0)

                unif4 = np.random.uniform(low=0, high=1, size=1)

                # Acceptance step
                if np.log(unif4) <= alphamh2:
                    b = bmh
                    arb = arb+1
                    
        if (iter0 % thinning == 0) & (iter0 >= burnin):
            iter1 = iter1 + 1
            sig2epssample[iter1-1,:] = sig2eps
            sig2thesample[iter1-1] = sig2the
            rhosample[iter1-1] = rho
            asample[iter1-1] = a
            bsample[iter1-1] = b
            msample[iter1-1,:] = m
            memorygn[iter1-1,:] = gn

            if level+trend+seasonality == 0:
                sig2alphasample[iter1-1,:] = sig2alpha
            elif level+trend+seasonality == 3:
                sig2betasample[iter1-1,:] = sig2beta
            else:
                sig2alphasample[iter1-1,:] = sig2alpha
                sig2betasample[iter1-1,:] = sig2beta

        if indlpml != 0:
            if (iter0 % 10 == 0) & (iter0 >= burnin):
                iter2 = iter2 + 1
                for i in range(0,n):
                    if level+trend+seasonality == 0:
                        for j in range(0,m):
                            auxlpml[iter2-1,i] = auxlpml[iter2-1,i] + ((nstar[j]-a)/(b+n))*scipy.stats.multivariate_normal.pdf(mydata[:,i], ((Z.dot(alpha[:,i])) + thetastar[:,j]), np.diag(np.repeat(sig2eps[i],T)))

                        sigmaeps = np.diag(np.repeat(sig2eps[i],T))
                        invsigmaeps = np.diag(np.repeat(1/sig2eps[i],T))

                        Q = sigmaeps + R
                        Qinv = inv(Q) 

                        Winv = Qinv
                        W = Q

                        auxlpml[iter2-1,i] = auxlpml[iter2-1,i] + ((b+(a*m))/(b+n))*scipy.stats.multivariate_normal.pdf(mydata[:,i], (Z.dot(alpha[:,i])), W)

                    elif level+trend+seasonality == 3:
                        for j in range(0,m):
                            auxlpml[iter2-1,i] = auxlpml[iter2-1,i] + ((nstar[j]-a)/(b+n))*scipy.stats.multivariate_normal.pdf(mydata[:,i], (X.dot(betastar[:,j]) + thetastar[:,j]), np.diag(np.repeat(sig2eps[i],T)))

                        sigmaeps = np.diag(np.repeat(sig2eps[i],T))
                        invsigmaeps = np.diag(np.repeat(1/sig2eps[i],T))

                        Q = sigmaeps + R
                        Qinv = inv(Q)

                        Vinv = np.transpose(X).dot(Qinv).dot(X) + invsigmabeta
                        V = inv(Vinv)
                        Winv = Qinv + (Qinv.dot(X).dot(V).dot(np.transpose(X)).dot(Qinv))
                        W = inv(Winv)

                        auxlpml[iter2-1,i] = auxlpml[iter2-1,i] + ((b+(a*m))/(b+n))*scipy.stats.multivariate_normal.pdf(mydata[:,i], np.zeros(T), W)

                    else:
                        for j in range(0,m):
                            auxlpml[iter2-1,i] = auxlpml[iter2-1,i] + ((nstar[j]-a)/(b+n))*scipy.stats.multivariate_normal.pdf(mydata[:,i], (Z.dot(alpha[:,i]) + X.dot(betastar[:,j]) + thetastar[:,j]), np.diag(np.repeat(sig2eps[i],T)))

                        sigmaeps = np.diag(np.repeat(sig2eps[i],T))
                        invsigmaeps = np.diag(np.repeat(1/sig2eps[i],T))

                        Q = sigmaeps + R
                        Qinv = inv(Q)

                        Vinv = np.transpose(X).dot(Qinv).dot(X) + invsigmabeta
                        V = inv(Vinv)
                        Winv = Qinv + (Qinv.dot(X).dot(V).dot(np.transpose(X)).dot(Qinv))
                        W = inv(Winv)

                        auxlpml[iter2-1,i] = auxlpml[iter2-1,i] + ((b+(a*m))/(b+n))*scipy.stats.multivariate_normal.pdf(mydata[:,i], Z.dot(alpha[:,i]), W)

        iter0 = iter0 + 1
        if iter0 % 50 == 0:
            print("Iteration Number: ", iter0, "Progress: ", round((iter0/maxiter),2)*100,"% \n")
##### END OF GIBBS SAMPLING #####
        

    # Calculation of acceptance rates and similarities matrix
    arrho = arrho/iter0
    ara = ara/iter0
    arb = arb/iter0
    sim = sim/iter1

    dist = np.zeros(CL)

    # Calculating the distance between each cluster configuration to the similarities matrix
    for i in range(0,CL):
        aux4 = memory[(i*n):((i+1)*n),:] - sim
        dist[i] = np.linalg.norm(aux4)

    # Determining which cluster configuration minimizes the distance to the similarities matrix
    mstar = msample[np.argmin(dist)]
    gnstar = memorygn[np.argmin(dist),:]

    ##### HM MEASURE CALCULATION #####
    HM = 0

    for j in range(0,mstar[0].astype(int)):
        cc = np.where(gnstar == j)[0]
        HM1 = 0

        if len(cc) > 1:
            for i1 in range(0,len(cc)):
                for i2 in range(0,i1):
                    HM1 = HM1 + sum((mydata[:,cc[i2]] - mydata[:,cc[i1]])**2)
            HM = HM + (2/(len(cc)-1))*HM1

    
	##### PRINT FINAL CLUSTER ASSIGNMENTS AND HM MEASURE #####
    print("Number of groups of the chosen cluster configuration: ", mstar[0].astype(int))
    for i in range(0,mstar[0].astype(int)):
        print("Time series in group ", i, np.where(gnstar == i)[0].astype(int), "\n")

    print("HM Measure: ", HM)

    if indlpml != 0:
        auxlpml = 1/auxlpml
        cpo = auxlpml.mean(axis=0)
        cpo = 1/cpo
        lpml = sum(np.log(cpo))
     
    ##### PLOT FINAL CLUSTER ASSIGNMENTS (ONE PLOT PER CLUSTER)#####
    for j in range(0, mstar[0].astype(int)):
        plt.figure()
        plt.axes([0, 0, 1, 1])
        cc_plot = np.where(gnstar == j)[0]
        plt.xlabel('Time Period')
        plt.ylabel('Scaled Value')
        title = "Group " + str(j)
        plt.title(title)
        plt.plot(mydata[:,cc_plot], c=np.random.rand(3))
        plt.show()
