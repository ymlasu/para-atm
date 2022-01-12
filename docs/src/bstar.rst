B-STAR
======

B-STAR is the abbreviation of Bayesian Spatio-Temporal grAph transformeR. `B-STAR <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3981312>`__ is an advaned deep learning model developed for multi-aircraft trajectory prediction. B-STAR uses IFF format ASDE-X near-terminal flight data for neural network training. The model has the following functionality:

* Graph Structured Transformer Network for Multi-Aircraft Interactions 
* Variational Bayesian Deep Learning for Uncertainty Quantification

A detailed demonstration of B-STAR can be found `here <https://github.com/ymlasu/para-atm-collection/tree/master/air-traffic-prediction/MultiAircraftTP>`__


.. py:module:: paraatm.bstar
para-atm B-STAR module
----------------------
B-STAR is a separate packed module in para-atm. :py:func:`~paraatm.bstar.trainval` is the interface function for user to perform desired tasks such as training a model with desired parameters, and testing with a pre-trained model.

.. autofunction:: paraatm.bstar.trainval
To Train a Model 
----------------
The training of a B-STAR model can be accessed by calling :py:func:`~paraatm.bstar.trainval` in the terminal, with the parameters defined above. Here is an example,

.. code:: shell

   python trainval.py --num_epochs 300 --start_test 250 --neighbor_thred 10 --skip 5 --seq_length 20 --obs_length 12 --pred_length 8 --learning_rate 0.0015 --sample_num 20

The trained model and saved test results will be saved in :code:`./output`. 


To Test a Pre-Trained Model
---------------------------
The testing of a B-STAR model will load a pre-trained best test performance model, say the model saved at epoch 258 in this example. The command-line interface to start the test will be,

.. code:: shell

   python trainval.py --test_set atl0807 --phase test --load_model 258


