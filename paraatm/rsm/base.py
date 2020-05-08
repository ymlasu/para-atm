import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class ResponseSurface:
    """Base class for response surface models

    Derived classes should:

    * Implement an `__init__` method that fits the model and calls
      `super().__init__`
    * Implement a `__call__` method for making predictions.  See
      :py:meth:`paraatm.rsm.gp.SklearnGPRegressor.__call__`.
    """

    def __init__(self, X, Y):
        self.X = X
        self.Y = Y
        self.num_inputs = np.size(X, 1)
    
    @staticmethod
    def _bounds_from_range_factor(xdata, range_factor):
        """Determine variable bounds based on given data
        
        Parameters
        ----------
        xdata : array
            1d or 2d array of training data, used to determine
            appropriate plotting bounds
        range_factor : float
            fraction of data range to use for bounds
        """
        xr = xdata.max(axis=0) - xdata.min(axis=0)
        xc = xdata.min(axis=0) + 0.5 * xr
        lb = xc - 0.5 * xr * range_factor
        ub = xc + 0.5 * xr * range_factor
        return lb, ub

    def plot(self, ax=None, lb=None, ub=None, range_factor=1.1, ci=True, show_data=True, input_vals=None, ivar=None, color=None, legend=True, ncol_leg=3):
        """Create 1D response surface plots
        
        By default, plot 1D curves of all variables on the same graph,
        but can also plot individual curves or subsets.

        Parameters
        ----------
        ax : matplotlib.axes or None
            Axis to plot on.  If None, create new axis.
        lb : float
            Lower bound, only supported for single-variable plot
        ub : float
            Upper bound, only supported for single-variable plot
        range_factor : float 
            Factor used to determine default plotting range.  The
            plotting range is determined as a multiple of the data
            range.
        ci : bool
            Whether or not to plot confidence intervals for 1-D plots
        show_data : bool
            Whether to plot the training data.  For slice plots,
            training data are projected
        input_vals : array
            Values to use for non-varying inputs (default to mean of
            training data)
        ivar : int or list of ints
            Variable index to plot.  Can be scalar or a list.  Default
            is to plot all variables.
        color : str
            Plotting color, for single-variable plots only
        legend : bool
            Whether to include legend
        ncol_leg : int
            Number of columns to use for formatting legend
        """
        NGRID_1D = 200

        d = self.num_inputs

        X,Y = self.X, self.Y

        if (input_vals is not None) and len(input_vals) != d:
            raise ValueError('size mismatch for input_vals')
        elif (lb is not None) or (ub is not None):
            if (ivar is None) and (d>1):
                raise ValueError('bounds only supported for single-variable plots')

        if input_vals is None:
            input_vals = X.mean(axis=0)

        if ivar is None:
            plot_vars = range(d)
        else:
            if hasattr(ivar, '__getitem__'):
                plot_vars = ivar
            else:
                plot_vars = [ivar]
        # Validate user-provided ivar
        if not set(plot_vars) <= set(np.arange(d)):
            raise ValueError('invalid variable index')

        user_lb, user_ub = lb, ub

        if ax is None:
            f, ax = plt.subplots()

        for i,ivar in enumerate(plot_vars):
            xdata = X[:,ivar]
            lb, ub = self._bounds_from_range_factor(xdata, range_factor)
            if user_lb is not None:
                lb = user_lb
            if user_ub is not None:
                ub = user_ub
            # Plot prediction
            xvals = np.linspace(lb,ub,NGRID_1D)
            Xvals = np.tile(input_vals, (NGRID_1D, 1))
            Xvals[:,ivar] = xvals
            if ci:
                ymean, ystd = self(Xvals, return_stdev=True)
            else:
                # Separated this case, since user-specified cor params
                # cause warning for each call to evaluate(var=1)
                ymean = self(Xvals)

            # Get x-plotting coordinates
            if len(plot_vars) == 1:
                xplot = xvals
            else:
                xplot = np.linspace(-range_factor,range_factor,NGRID_1D)

            if len(plot_vars) > 1:
                color = None
            ax.plot(xplot, ymean)
            # Plot confidence intervals
            if ci:
                ax.fill_between(xplot,ymean+1.96*ystd,ymean-1.96*ystd, color=color, alpha=0.2)
            # Plot training data
            if show_data and len(plot_vars)==1:
                ax.plot(xdata,Y,'ro')

            if len(plot_vars) == 1:
                ax.set_xlim(lb,ub)
            else:
                ax.set_xlim(-range_factor, range_factor)
                ax.set_xlabel('Standardized input')
            ax.set_ylabel('Output')

        if legend and len(plot_vars)>1:
            ax.legend( ['{}'.format(i+1) for i in plot_vars], ncol=ncol_leg, loc='best' )

    def surface_plot(self, ax=None,lb=None, ub=None, range_factor=1.1, ngrid=40, show_data=True, input_vals=None, slice_vars=None, surf_args=None):
        """ Create 2D surface plot

        Parameters
        ----------
        ax : matplotlib.axes or None
            Axis to plot on.  If None, create new axis
        lb : array
            Lower bound to use for each variable
        ub : array
            Upper bound to use for each variable
        range_factor : float
            Factor used to determine default plotting range.  The
            plotting range is determined as a multiple of the data
            range.
        ngrid : int
            Grid density used in each dimension
        show_data : bool
            Whether to plot training data
        input_vals : array
            Array of input values, required when plotting a slice of a
            surface with more than two input variables.
        slice_vars : tuple
            Length-2 tuple with indices of the variables to plot.
            Required when the response surface has more than two input
            variables.
        surf_args : dict 
            Additional keyword arguments to send to Axes3D.plot_surface

        Returns
        -------
        matplotlib.axes
        """

        d = self.num_inputs

        if d < 2:
            raise RuntimeError('surface plot not valid for 1D response surfaces')
        elif (input_vals is not None) and len(input_vals) != d:
            raise ValueError('size mismatch for input_vals')
        elif slice_vars is not None:
            if len(slice_vars)!=2:
                raise ValueError('slice_vars must be length-2')
            elif not set(slice_vars) <= set(np.arange(d)):
                raise ValueError('invalid slice index')
        elif (slice_vars is None) and d>2:
            raise ValueError('must provide slice_vars')

        X,Y = self.X, self.Y

        if slice_vars==None:
            ivar = np.array([0,1])
        else:
            ivar = np.array(slice_vars)

        if input_vals is None:
            input_vals = X.mean(axis=0)
        else:
            input_vals = np.array(input_vals)

        Xvar = X[:,ivar] # Training data for varying inputs only

        _lb, _ub = self._bounds_from_range_factor(Xvar, range_factor)
        if lb is None:
            lb = _lb
        if ub is None:
            ub = _ub

        # Evaluate over a uniform grid
        xvals = np.linspace(lb[0],ub[0],ngrid)
        yvals = np.linspace(lb[1],ub[1],ngrid)
        XX,YY = np.meshgrid(xvals,yvals)
        Z = np.zeros( (ngrid,ngrid) )
        input_vec = input_vals.copy()
        for i in range(ngrid):
            for j in range(ngrid):
                input_vec[ivar] = [XX[i,j],YY[i,j]]
                Z[i,j] = self(input_vec)

        # Plot surface
        if ax is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
        if show_data:
            # Data don't show up well on top of surface plot
            ax.plot_wireframe(XX,YY,Z)
        else:
            kwargs = {'rstride':1, 'cstride':1, 'cmap':plt.cm.jet}
            if surf_args is not None:
                kwargs.update(surf_args)
            ax.plot_surface(XX,YY,Z,**kwargs)

        # Plot training data
        if show_data:
            ax.scatter(Xvar[:,0], Xvar[:,1], Y)

        return ax
