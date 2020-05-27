import numpy as np

from sklearn import gaussian_process
from sklearn.gaussian_process.kernels import WhiteKernel, RBF
from sklearn import preprocessing

from paraatm.rsm.base import ResponseSurface

class SklearnGPRegressor(ResponseSurface):
    """Gaussian Process regression using scikit-learn"""
    def __init__(self, X, Y, noise=False, n_restarts_optimizer=10, alpha=1e-10, kernel=None, optimizer='fmin_l_bfgs_b'):
        """Create GP regression instance and fit to training data

        Parameters
        ----------
        X : array
            2d array of input values, with each row representing a
            case and each column a variable
        Y : array
            1d array of output values
        noise : bool
            Whether the outputs are observed with noise.  If True, the
            noise variance is estimated as part of the fitting.
            Additionally, scikit-learn includes the noise in the
            prediction standard deviation.
        n_restarts_optimizer : int
            Number of times optimizer is restarted using randomly
            selected initial points
        alpha : float
            Value added to diagonal of covariance matrix during
            fitting.  Unlike the noise variance that can be fit
            through the WhiteKernel, the alpha value is not included
            in the predicted standard deviation.
        kernel : kernel object
            Kernel specifying the covariance function of the GP.  If
            None, RBF (a.k.a., squared exponential) is used with
            unique length parameters for each dimension.
        optimizer : str, callable, or None
            Passed on to sklearn.  In particular, None can be used to
            fix the kernel parameters instead of optimizing them.
        """

        super().__init__(X, Y)

        # Scale x values so that we can use the same starting point
        # for the correlation parameters
        self.x_scaler = preprocessing.StandardScaler().fit(X)

        # Scale the y-values so that we can use same starting point
        # for process variance (using the built in normalize_y option
        # appears to only handle centering (prior mean), but not
        # scaling).  Could use StandardScalar for Y also, but
        # cumbersome to use with 1D data, so just do it manually.
        self.y_mean = np.mean(Y)
        self.y_std = np.std(Y)
        Y_transformed = (Y-self.y_mean) / self.y_std
        
        if kernel is None:
            # Use a default kernel
            kernel = 1.0 * RBF(np.repeat(1, self.num_inputs), (1e-2, 1e2))
            if noise:
                kernel += WhiteKernel(noise_level=0.05)

        self.gp = gaussian_process.GaussianProcessRegressor(kernel=kernel, alpha=alpha, n_restarts_optimizer=n_restarts_optimizer, normalize_y=False, optimizer=optimizer).fit(self.x_scaler.transform(X), Y_transformed)

    def __call__(self, X, return_stdev=False):
        """Compute predicted mean and standard deviation (optionally) at specified input(s)

        Parameters
        ----------
        X : array, 1d or 2d
            Input values, either as a single point (1d array) or a 2d
            array containing a set of points
        return_stdev : bool
            Whether to return standard deviation of the prediction, in
            addition to the mean.
        
        Returns
        -------
        tuple, float, or array
            The return value is either a tuple containing the mean and
            standard deviation (if `return_stdev==True`) or the mean
            value only.  If `ndim(X)==2`, then the mean and standard
            deviations are returned as arrays, otherwise they are
            floats.
        """
        ndim = np.ndim(X)
        X = np.atleast_2d(X)
        results = self.gp.predict(self.x_scaler.transform(X), return_std=return_stdev)
        if ndim == 1:
            # Convert results back to scalars
            if return_stdev:
                results = results[0][0], results[1][0]
            else:
                results = results[0]
        # Un-standardize Y values
        if return_stdev:
            results = results[0]*self.y_std + self.y_mean, results[1]*self.y_std
        else:
            results = results*self.y_std + self.y_mean
        return results

    @staticmethod
    def _rsquared(actuals, preds):
        """Compute R-squared value from actuals and predictions"""
        
        SST = sum( (actuals - np.mean(actuals))**2 )
        SSE = sum( (actuals - preds)**2 )

        return 1.0 - SSE/SST

    def fit_rsquared(self):
        """Get fit R-squared value"""

        preds = self(self.X, return_stdev=False)

        return self._rsquared(self.Y, preds)

    def loo_rsquared(self):
        """Get leave-one-out R-squared value
        
        Kernel parameters and normalization constants are not changed.
        The intent is to test holding out the observations but not
        re-fitting the kernel parameters.
        """

        Xtrans = self.x_scaler.transform(self.X)
        Ytrans = (self.Y - self.y_mean) / self.y_std

        preds = []

        for i in range(len(Ytrans)):
            X = np.delete(Xtrans, i, axis=0)
            Y = np.delete(Ytrans, i)
        
            gp = gaussian_process.GaussianProcessRegressor(kernel=self.gp.kernel_, alpha=self.gp.alpha, normalize_y=False, optimizer=None).fit(X, Y)
            preds.append( gp.predict([Xtrans[i,:]], return_std=False)[0] )


        return self._rsquared(Ytrans, np.array(preds))


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    # Simple demonstration of GP regression with 1 input

    # X = np.linspace(0,10,8)
    X = np.array([1., 3., 5., 6., 7., 8.])
    Y = X * np.sin(X)
    X = X[:,np.newaxis] # Make input array 2d

    # Use n_restarts_optimizer=0 to get reproducible behavior
    gp = SklearnGPRegressor(X, Y, n_restarts_optimizer=0)

    print('fit R-squared:', gp.fit_rsquared())
    print('cross-val R-squared:', gp.loo_rsquared())

    gp.plot()

    plt.show()
