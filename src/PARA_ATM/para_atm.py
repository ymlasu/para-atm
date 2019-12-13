"""Provides entry point main()"""

#__version__ = "0.2.0"

import argparse

from PARA_ATM.Application import LaunchApp
from PARA_ATM.io.utils import read_data_file
from PARA_ATM.plotting.plotting import plot_trajectory

def main():

    parser = argparse.ArgumentParser(description="PARA_ATM command-line interface.  Try 'para_atm <cmd> -h' for information on how to use a particular command")
    #parser.add_argument('-v','--version', action='version', version='%(prog)s '+__version__)

    subparsers = parser.add_subparsers(title='command', dest='command', help='available para_atm commands')

    # set_defaults is used to associate a function to call with each subparser mode

    p_app = subparsers.add_parser('app', help='launch standalone graphical application')
    p_app.set_defaults(func=LaunchApp.main)

    p_plot = subparsers.add_parser('plot', help='plot flight trajectory for a specified data file')
    p_plot.add_argument('file', help='data file to plot (NATS or IFF format)')


    args = parser.parse_args()


    # At this point, could just call args.func(), but some commands may
    # have different signatures
    if args.command == 'app':
        LaunchApp.main()
    elif args.command == 'plot':
        df = read_data_file(args.file)
        plot_trajectory(df)
