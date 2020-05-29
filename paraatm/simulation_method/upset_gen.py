"""
NASA University Leadership Initiative program
Information fusion for real-time national air transportation system prognostics under uncertainty

    Upset Scenario Generator (upgen) sub module 
    - Upset cases were investigated from NASA Generic Transport Model (GTM)
    - Case 1: rudder upset
    - Case 2: left aileron upset; spiral dive
    - Able to adjust upset rate, duration, severity

    @author: Hyunseong Lee, Adaptive Intelligent Materials & Systems (AIMS) Center,
             Arizona State University
    
    Last modified on 5/25/2020
"""

import sys
import numpy as np
from scipy import signal

class upgen:
    def __init__(self, alt_ft, alt_rate_coef, tas_knots, tas_rate_coef, course_deg, course_rate_coef, duration):
        self.alt_ft = alt_ft
        self.alt_rate_coef = alt_rate_coef
        self.tas_knots = tas_knots
        self.tas_rate_coef = tas_rate_coef
        self.course_deg = course_deg
        self.course_rate_coef = course_rate_coef
        self.duration = duration

        check_alt = self.alt_ft - self.alt_rate_coef*(self.duration**2)
        if check_alt < 0:
            raise RuntimeError('Set proper alt rates or duration')

            
    # Case 1: rudder upset
    def rudder_upset(self):
        alt_post = np.empty([self.duration,1])
        tas_post = np.empty([self.duration,1])
        course_post = np.empty([self.duration,1])
              
        for i in range(0, self.duration):

            # Altitude decreasing - quadratic form
            alt_post[i] = self.alt_ft - self.alt_rate_coef*(i**2)
            
            # True airspeed decreasing - quadratic form
            tas_post[i] = self.tas_knots - self.tas_rate_coef*(i**2)
            
            # Course angle changing - linear form 
            course_post[i] = self.course_deg*(1 + self.course_rate_coef*i)
            
        return alt_post, tas_post, course_post

    # Case 2: left aileron upset
    def aileron_upset(self):
        alt_post = np.empty([self.duration,1])
        tas_post = np.empty([self.duration,1])
        course_post = np.empty([self.duration,1])

        for i in range(0, self.duration):

            # Altitude decreasing - quadratic form
            alt_post[i] = self.alt_ft - self.alt_rate_coef*(i**2)
            
            # True airspeed decreasing - quadratic form
            tas_post[i] = self.tas_knots + self.tas_rate_coef*(i**2)
        
        # Course angle changing - triangular signal form
        temp_dur = np.linspace(0, self.duration+100, self.duration+100)
        triangle = 180*signal.sawtooth(2 * np.pi * self.course_rate_coef * temp_dur, 0)

        temp_ind = []; sub_triangle = []; min_ind = []; 
        
        if self.course_deg > 0:
            temp_ind = np.where(triangle[0:self.course_rate_coef]>0)[0]
            sub_triangle = abs(triangle[temp_ind] - self.course_deg)
            min_ind = int(np.where(sub_triangle == sub_triangle.min())[0])
            
        else:
            temp_ind = np.where(triangle[0:self.course_rate_coef]<0)[0]
            sub_triangle = abs(triangle[temp_ind] - self.course_deg)
            min_ind = int(np.where(sub_triangle == sub_triangle.min())[0])
            
        post_ini_ind = temp_ind[min_ind]
        course_post = triangle[post_ini_ind:self.duration+post_ini_ind]
        
        return alt_post, tas_post, course_post
