"""
NASA University Leadership Initiative program
Information fusion for real-time national air transportation system prognostics under uncertainty

    Flight Health Monitor (fhm) sub module
    - Calculate Mahalanobis distance to detect aircraft upsets
    - Upset metric = 1: upset
    - Upset metric = 0: normal

    @author: Hyunseong Lee, Adaptive Intelligent Materials & Systems (AIMS) Center,
             Arizona State University
    
    Last modified on 5/25/2020
"""

import numpy as np

class fhm:    
    def __init__(self, rec_error, mean, cov, cov_inverse, th_Mahal_dist):        
        self.rec_error = rec_error
        self.mean = mean
        self.cov = cov 
        self.cov_inverse = cov_inverse
        self.th_Mahal_dist = th_Mahal_dist
     
    def rt_fhm(self):        
        ctrd_error = self.rec_error - self.mean
        Mahal_dist = np.sqrt(np.sum(ctrd_error * self.cov_inverse * ctrd_error.T))
        
        if Mahal_dist > self.th_Mahal_dist:
            upset_metric = 1
            print("################ Upset detected ################")
        else:
            upset_metric = 0
        
        return Mahal_dist, upset_metric