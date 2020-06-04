Function MFAC_paraatm in MFAC_paraatm
'''
This is a training algorithm for some flight plans that suffer from a risk of collision.
:param fp_file: the file handle of the current flight plans file that suffer from a risk of collision
:param mfl_file: mfl file for the fp_file
:param numAC: number of aircrafts involved in the collision avoidance
:param sim_time: simulation time for each episode in NATS, suggest to be the cruise time
:param maxEpisodes: number of episodes of training, the larger this parameter is, the better the result could be, however that may leads to longer training time
:param dt: dt of NATS simulation
:return: The trained parameters of the neural network is save in directory "/Data"
'''

test case: run test_MFAC_paraatm.py directly.