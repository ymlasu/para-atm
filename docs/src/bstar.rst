B-STAR
======

B-STAR is the abbreviation of Bayesian Spatio-Temporal grAph transformeR. `B-STAR <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3981312>`__ is an advanced deep learning model for multi-aircraft trajectory prediction. B-STAR model is a neural network model trained using IFF format ASDE-X near-terminal flight data. The model supports the following functionalities:

* Graph Structured Transformer Network for Multi-Aircraft Interactions 
* Variational Bayesian Deep Learning for Uncertainty Quantification

A detailed demonstration of B-STAR can be found `here <https://github.com/ymlasu/para-atm-collection/tree/master/air-traffic-prediction/MultiAircraftTP>`__


.. py:module:: paraatm.bstar

The para-atm B-STAR module
--------------------------
B-STAR is a separate module in para-atm. :py:func:`~paraatm.bstar.trainval` is the interface function for user to perform desired tasks such as training a model with desired parameters, and testing a pre-trained model.

.. autofunction:: paraatm.bstar.trainval

The B-STAR module can be run with a number of options/arguments, and is supported by a :py:mod:`parser` function to identify the arguments provided by the user and assign default values. These arguments include the following:

- Core functionalities for identifying input/output directories and processing configuration

.. code-block:: python

    parser = argparse.ArgumentParser(description='BSTAR')
    parser.add_argument('--dataset', default='iffatl')
    parser.add_argument('--save_dir')
    parser.add_argument('--model_dir')
    parser.add_argument('--config')
    parser.add_argument('--using_cuda', default=False, type=ast.literal_eval)

- Locations of files containing datasets used for model training/testing

.. code-block:: python

    parser.add_argument('--test_set', default='atl0807', type=str,
                        help='Set this value to [atl0801, atl0802, atl0803, atl0804, atl0805, atl0806, atl0807] foe different test set')
    parser.add_argument('--base_dir', default='.', help='Base directory including these scripts.')
    parser.add_argument('--save_base_dir', default='./output/', help='Directory for saving caches and models.')
    parser.add_argument('--phase', default='train', help='Set this value to \'train\' or \'test\'')

- Options for training a new model or loading an existing (pre-trained) model

.. code-block:: python

    parser.add_argument('--train_model', default='bstar', help='Your model name')
    parser.add_argument('--load_model', default=None, type=str, help="load pretrained model for test or training")

- Model name, size of training data (number of total sequantial batches), time horizon for model training and model testing 

.. code-block:: python

    parser.add_argument('--model', default='bstar.BSTAR')
    parser.add_argument('--seq_length', default=20, type=int)
    parser.add_argument('--obs_length', default=12, type=int)
    parser.add_argument('--pred_length', default=8, type=int)
    parser.add_argument('--batch_around_ped', default=256, type=int)
    parser.add_argument('--batch_size', default=7, type=int)
    parser.add_argument('--test_batch_size', default=4, type=int)
    parser.add_argument('--show_step', default=100, type=int)

- Training parameters (epochs, burn-in testing, sample number, neighbor threshold, learning rate,  ... etc.)

.. code-block:: python

    parser.add_argument('--start_test', default=250, type=int)
    parser.add_argument('--sample_num', default=20, type=int)
    parser.add_argument('--num_epochs', default=300, type=int)
    parser.add_argument('--ifshow_detail', default=True, type=ast.literal_eval)
    parser.add_argument('--ifsave_results', default=False, type=ast.literal_eval)
    parser.add_argument('--randomRotate', default=True, type=ast.literal_eval,
                        help="=True:random rotation of each trajectory fragment")
    parser.add_argument('--neighbor_thred', default=10, type=int)
    parser.add_argument('--learning_rate', default=0.0015, type=float)

- Prediction time interval and precision

.. code-block:: python

    parser.add_argument('--clip', default=1, type=int)
    parser.add_argument('--skip', default=5, type=int)

To Train a Model 
----------------
The training of a B-STAR model can be accessed by calling :py:func:`~paraatm.bstar.trainval` in the terminal, with the parameters defined above. Here is an example,

.. code:: shell

   python trainval.py --num_epochs 300 --start_test 250 --neighbor_thred 10 --skip 5 --seq_length 20 --obs_length 12 --pred_length 8 --learning_rate 0.0015 --sample_num 20

In this example, the model will be trained over 300 epochs using a neighborhhood threshold = 10 and a learning rate = 0.0015. The model will be trained using 12 data batches, with 8 additional batches used for testing prediction accuracy.  The trained model and saved test results will be saved in :code:`./output`. 


To Test a Pre-Trained Model
---------------------------
Testing a B-STAR model starts by loading the pre-trained model with best perdiction performance. The command-line interface to start the test takes the form:

.. code:: shell

   python trainval.py --test_set atl0807 --phase test --load_model 258

In this example:
:py:mod:`--test_set atl0807` defines the test data set
:py:mod:`--phase test`  runs the B-STAR in testing mode
:py:mod:`--load_model 258`--load_model 258 instructs B-STAR to load the model saved at epoch 258 