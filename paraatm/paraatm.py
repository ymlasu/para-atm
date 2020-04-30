"""Provides entry point main()"""

#__version__ = "0.2.0"

import argparse
import inspect
import os
import sys
import importlib

from paraatm.io.utils import read_data_file
from paraatm.plotting import plot_trajectory
from paraatm.io.nats import NatsSimulationWrapper
from paraatm.io.gnats import GnatsSimulationWrapper

def main():

    parser = argparse.ArgumentParser(description="para-atm command-line interface.  Try 'para-atm <cmd> -h' for information on how to use a particular command")
    #parser.add_argument('-v','--version', action='version', version='%(prog)s '+__version__)

    subparsers = parser.add_subparsers(title='command', dest='command', help='available para-atm commands')

    # set_defaults is used to associate a function to call with each subparser mode

    p_plot = subparsers.add_parser('plot', help='plot flight trajectory for a specified data file')
    p_plot.add_argument('file', help='data file to plot (NATS or IFF format)')

    p_nats = subparsers.add_parser('nats', help='run NATS simulation implemented via NatsSimulationWrapper')
    p_nats.add_argument('file', help='python module with a class that derives from NatsSimulationWrapper')
    p_nats.add_argument('--output', help='file to store nats results')
    p_nats.add_argument('--plot', action='store_true', help='plot results')

    p_gnats = subparsers.add_parser('gnats', help='run GNATS simulation implemented via GnatsSimulationWrapper')
    p_gnats.add_argument('file', help='python module with a class that derives from GnatsSimulationWrapper')
    p_gnats.add_argument('--output', help='file to store gnats results')
    p_gnats.add_argument('--plot', action='store_true', help='plot results')


    args = parser.parse_args()


    # At this point, could just call args.func(), but some commands may
    # have different signatures
    if args.command == 'plot':
        df = read_data_file(args.file)
        plot_trajectory(df)
        
    elif args.command == 'nats' or args.command == 'gnats':
        dirname = os.path.dirname(os.path.abspath(args.file))
        sys.path.insert(0, dirname)
        module = importlib.import_module(os.path.basename(args.file).replace('.py',''))
        # Find appropriate classes in the user-specified module:
        if args.command == 'nats':
            classes = inspect.getmembers(module, lambda member: inspect.isclass(member) and issubclass(member, NatsSimulationWrapper) and member is not NatsSimulationWrapper)
            if len(classes) < 1:
                raise ValueError('no subclass of NatsSimulationWrapper found in {}'.format(args.file))
        else:
            classes = inspect.getmembers(module, lambda member: inspect.isclass(member) and issubclass(member, GnatsSimulationWrapper) and member is not GnatsSimulationWrapper)            
            if len(classes) < 1:
                raise ValueError('no subclass of GnatsSimulationWrapper found in {}'.format(args.file))
        class_name, the_class = classes[0] # Use the first available class
        print('Creating simulation from: {}'.format(class_name))
        sim = the_class() # Instatiate class
        df = sim(output_file=args.output) # Run simulation
        if args.plot:
            plot_trajectory(df)
