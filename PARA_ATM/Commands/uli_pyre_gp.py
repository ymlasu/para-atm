from __future__ import print_function

import GPy
import pyre
import numpy as np

class ReliabilityAnalysis:

    def __init__(self,capacity,demand):
        """ Set demand and capacity values for the airport
            Probabilities are from the pie chart showing the %age of time that the 
                airport is in each weather condition
            Values are taken from the tables that show the capacity of the airport
                under the various weather conditions
            Data from: https://www.faa.gov/airports/planning_capacity/profiles/media/SEA-Airport-Capacity-Profile-2018.pdf
            Envision this being replaced by a call to some database in the future
        """
        self.capacity_probs = capacity[0]
        self.capacity_vals = capacity[1]
        self.demand_mean = demand[0]
        self.demand_stdv = demand[1]
        # Define options this reliability problem
        self.options = pyre.AnalysisOptions()
        self.options.printResults(False)

    # Define response function
    # This is a simple demand-capacity computation
    def func(self,Demand,Dummy):
        """ Simple demand-capacity computation
            args:
                 Demand = the demand distribution
                 Dummy  = dummy variables
            returns:
                 PyRe input vector same length as Demand
        """

        n = np.size(Demand)
        # Create samples of Capacity
        Capacity = np.random.choice(self.capacity_vals,p=self.capacity_probs,size=(1,n))
        # Combine Demand & Capacity in to single array of shape expected by GPy
        xx = np.reshape(np.dstack((Capacity,Demand)),(n,2))
        # Evaluate the points using the GP
        yy = m.predict(xx)[0]
        # Return output vector in shape expected by PyRe
        return np.reshape(yy,(1,n))
    
    
    # Construct GP for response function
    # Sample the input space
    def construct_GP(self,nsam):
        """ Construct GP for response function
            args:
                 nsam = number of samples
            returns:
                 void, sets self.m to the new GP model
        """

        C = np.random.choice(self.capacity_vals,p=self.capacity_probs,size=(nsam,1))
        D = np.random.uniform(self.demand_mean-3*self.demand_stdv,self.demand_mean+3*self.demand_stdv,(nsam,1))
        X = np.reshape(np.dstack((C,D)),(nsam,2))
        # Evaluate response function at each sample
        Y = C - D
        # Create GP model (use all default settings for now)
        self.m = GPy.models.GPRegression(X,Y)
        self.m.optimize()
        
    
    def get_stochastic_model(self):
        """ Create random variables and define distributions
            args:
                 none
            returns:
                 void, sets self.stochastic_model to the new variable object
        """

        self.stochastic_model = pyre.StochasticModel()
             
        # Define demand distribution
        # Currently based on simple visual inspection of SEA Arrival/Departure plots
        self.stochastic_model.addVariable( pyre.Normal('Demand',self.demand_mean,self.demand_stdv) )
                          
        # Define capacity distribution
        # Just a dummy variable. Create our own discrete RV in response function
        self.stochastic_model.addVariable( pyre.Uniform('Dummy',0,1,1) )
    

    def define_limit_state(self,function=self.func):
        """ Define reliability problem
            args:
                 function = option to pass arbitrary limit state function
                            defaults to the one defined above
            returns:
                void, sets self.limit_state to the new limit state
        """

        # Compute P[Demand > Capacity] or P[Demand-Capacity > 0]
        self.limit_state = pyre.LimitState(function)
    
    def analyze(self,nsam,custom_limit_state=None,analysis_type='MC'):
        """ Main entry point of the object
            args:
                nsam = number of samples for Gaussian process model
                custom_limit_state = arbitrary limit state function
                                     or something evaluating to False
                analysis_type = type of analysis to perform
                                defaults to monte carlo
            returns:
                analysis object
        """

        construct_GP(nsam)
        get_stochastic_model()
        if custom_limit_state:
            define_limit_state(custom_limit_state)
        else:
            define_limit_state()
        # Execute the analysis
        analysis = None
        if analysis_type == 'MC':
            analysis = pyre.CrudeMonteCarlo(analysis_options=self.options, 
                     stochastic_model=self.stochastic_model, limit_state=self.limit_state)
        #TODO: add more types of analysis

        # Print some useful output
        print("pf: ", analysis.getFailure())
        return analysis
