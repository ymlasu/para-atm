import pandas as pd
import numpy as np
import time as tm
import csv
import shutil
import os

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

class FAA_Parser(object):

    def __init__(self, reg_num, time, chunk_size):

        self.time = time
        self.reg_num = reg_num
        self.chunk_size = chunk_size

        # specific row numbers to keep
        self.rows = []

        # specific colomn numbers to keep
        self.cols = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]  # include lat and lon

        # track point is the array to store trajectories

    def count_rows(self):

        t0 = tm.time()
        n = sum(1 for line in open('IFF_' + self.time + '.csv'))
        print ("loaded " + str(n) + " rows of data")
        print('Elapsed time : ', tm.time() - t0)

    def get_flight_plan(self):

        # chunk number index
        i = 0

        df = pd.read_csv('IFF_' + self.time + '.csv', chunksize=self.chunk_size,
                         iterator=True, names=range(0, 15), low_memory=False)

        self.track_point = np.empty((0, 15))

        for chunk in df:

            i = i + 1
            print ("reading chunk number " + str(i))
            chunk[2] = chunk[2].apply(str)
            self.rows = []
            self.rows.extend(chunk.index[chunk[2] == self.reg_num])
            if len(self.rows) != 0:
                data = chunk.ix[self.rows][self.cols]
                self.track_point = np.concatenate((self.track_point, data), axis=0)

    def save_csv(self, name):

        my_df = pd.DataFrame(self.track_point)
        filename=str(name).zfill(4)
        my_df.to_csv("2020csv/" + str(filename) + '.csv', index=False, header=False)


if __name__ == '__main__':
    FileName = "2020csv"
    createFolder('./' + str(FileName) + '/')

    time = '2020'


    print ("Reading FAA_" + time + ".csv")

    chunk_size = 1e6
    print ("Chunk size is " + str(int(chunk_size)))

    with open("IFF_2020_dailynums.csv") as register_num_list:
        reader = csv.reader(register_num_list, delimiter=',')
        for i, line in enumerate(reader):

            print ("Flight register number {} is {}".format(i, str(line[0])))

            fun = FAA_Parser(str(line[0]), time, chunk_size)
            fun.get_flight_plan()
            fun.save_csv(i)
            del fun
