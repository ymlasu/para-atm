import os

class Get_Average_Speed (object):
    def __init__(self):
        # os.system("python ./Split_Aircraft_0.py")
        os.system("python ./Split_Aircraft_seperate_1.py")
        os.system("python ./Reshape_Information_2.py")
        os.system("python ./Distinguish_Aircraft_3.py")
        os.system("python ./Find_Ground_Operation_4.py")
        os.system("python ./MergeInformation_5.py")
        os.system("python ./History_Speed_6.py")


if __name__ == '__main__':
    g = Get_Average_Speed()