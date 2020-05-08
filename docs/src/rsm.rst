Response surface models
=======================

.. py:module:: paraatm.rsm

Response surface base class
---------------------------

.. autoclass:: paraatm.rsm.base.ResponseSurface
    :members:

Gaussian process regression
---------------------------

.. autoclass:: paraatm.rsm.gp.SklearnGPRegressor
    :members:
    :special-members:

Examples
^^^^^^^^

Here is an example showing a GP fit to a 1D function, with confidence bounds:

.. plot::
    :include-source:

    import matplotlib.pyplot as plt
    from paraatm.rsm.gp import SklearnGPRegressor

    x = np.array([1., 3., 5., 6., 7., 8.])
    y = x * np.sin(x)
    X = x[:,np.newaxis] # Make input array 2d

    # Use n_restarts_optimizer to get reproducible behavior
    gp = SklearnGPRegressor(X, y, n_restarts_optimizer=0)

    gp.plot()

    plt.show()


And an example of a 2D function, using :py:meth:`~paraatm.rsm.base.ResponseSurface.surface_plot`:

.. plot::
    :include-source:

    import matplotlib.pyplot as plt
    from paraatm.rsm.gp import SklearnGPRegressor

    np.random.seed(1)
    X = np.random.uniform(-2, 2, size=(30,2))
    Y = X[:,0] * np.exp(-X[:,0]**2 - X[:,1]**2)

    gp = SklearnGPRegressor(X, Y, n_restarts_optimizer=0)

    ax = gp.surface_plot()
    ax.view_init(17, -70)

    plt.show()

