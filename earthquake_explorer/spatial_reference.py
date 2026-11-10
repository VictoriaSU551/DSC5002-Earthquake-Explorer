"""Descriptive equal-area spherical reference; no seismicity null hypothesis."""
import numpy as np
from scipy.stats import qmc

def sphere_reference(power=14,seed=5002):
    u=qmc.Sobol(d=2,scramble=True,seed=seed).random_base2(power)
    return 360*u[:,0]-180,np.degrees(np.arcsin(2*u[:,1]-1))

def latitude_reference(latitudes,power=14,seed=5012):
    u=qmc.Sobol(d=2,scramble=True,seed=seed).random_base2(power)
    values=np.sort(np.asarray(latitudes))
    return 360*u[:,0]-180,values[np.minimum((u[:,1]*len(values)).astype(int),len(values)-1)]
