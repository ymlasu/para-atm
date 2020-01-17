# NASA ULI InfoFusion

## Introduction

Information fusion for real-time national air transportation system prognostics under uncertainty. This project highlights integration of two main software systems, PARA-ATM (Arizona State University), and NATS (Optimal Synthesis Inc).

## Installation

Note that [install_PARA-ATM.sh](install_PARA-ATM.sh) was originally developed to provide a single script to handle installation of Anaconda Python, dependencies, NATS, and database setup.  This script uses package management commands that are specific to the Ubuntu Linux operating system.  It is recommended to follow the instructions below instead, although new users may prefer the script as a "one-shot" setup.

In short, the steps are:
- Install Python 3
- From the `src` directory, run: `python setup.py develop`

The following sections provide further details.

### Install Python

The first step is to install Python 3 on the system.

#### Ubuntu Linux

On Ubuntu 18, this can be done using:

```
sudo apt install python3
```

#### Windows

There are different ways to install Python on Windows.  One approach is to use the Anaconda distribution.  In particular, the "miniconda" installation provides a minimal install, to which further packages can be added as necessary: https://docs.conda.io/en/latest/miniconda.html.  With Anaconda on Windows, it is common to use the default settings that do not add Python to the system `PATH` environment variable, in which case all Python commands are then done within the special command prompt provided by Anaconda.

### Virtual environments

Although not strictly necessary, it is recommended to create a Python virtual environment for PARA_ATM.  This way, all packages that are installed by PARA_ATM are isolated and will not interfere with packages that may be needed for other projects.

#### Virtual environment on Linux

These steps should apply to any Linux distribution.  We will install the virtual environment within a directory named `venv` under the home directory, and the virtual environment will be named `patm`.  However, any name and location for the virtual environment may be used.

``` shell
python3 -m venv ~/venv/patm
```

The above command creates the new virtual environment.  To activate the virtual environment, run:

``` shell
source ~/venv/patm/bin/activate
```
Upon activation, the command prompt will change to show the name of the virtual environment.  The above command can be added to the `~/.bashrc` file to automatically activate the virtual environment each time a new terminal is started.  To deactivate the virtual environment, type `deactivate`.

#### Virtual environment on Windows using Anaconda

Although the above approach can be used on Windows as well (see https://docs.python.org/3.8/library/venv.html for Windows-specific information), Anaconda provides functions that make virtual environments more convenient.  From the Anaconda prompt, use:

``` shell
conda create --name patm python=3.7
```

The virtual environment can then be activated directly, with no need to specify the path:

``` shell
conda activate patm
```

See https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html for more information about working with virtual environments in Anaconda.

### Install PARA_ATM Python package

Installation is handled via the `setup.py` script in the `src` directory.  If using a virtual environment, activate the appropriate virtual environment as described above.  Then navigate to the `src` directory and run the following command:

```
python setup.py develop
```

The `develop` command is similar to `install`, but instead of copying files into the installation directory, it creates a link to the source files.  This way, there is no need to reinstall when changes are made to PARA_ATM.

If the installation is not being performed within a virtual environment, the following command is recommended:

``` shell
python setup.py develop --user
```
The `--user` flag ensures that the dependencies installed by PARA_ATM do not interfere with system-wide Python packages installed via the package manager (i.e., `apt install`).

On Ubuntu 18, if the installation is not performed within a virtual environment, it will be necessary to replace the `python` command with `python3`.  This is because by default, `python` refers to `python2` on this system.


### Database setup (optional)

Setting up the database is optional.  Currently, the database only is required for the GUI application that is launched via `para_atm app`.

To set up the database on Ubuntu, first install the necessary packages:
``` shell
sudo apt install postgresql
sudo apt install pgadmin3
sudo apt install postgresql-contrib
```

Then run the setup script to configure the database:
``` shell
./dbSetup.sh
```

On other operating systems, the exact commands will differ, but the general steps are the same.  Refer to operating system specific instructions for installing postgresql.

### Install NATS (optional)

Installation of NATS is optional.  Refer to the NATS [README.txt](src/NATS/README.txt).  NATS may be distributed separately in the future.

## Testing

To test the PARA_ATM installation, run the following command from the `src` directory:

```
python -m unittest
```

## Usage

The PARA_ATM package may be used from within Python via `import PARA_ATM`, or through the command-line interface provided by the `para_atm` command.  For help with the command-line interface, run:

```
para_atm -h
```

If PARA_ATM was installed within a virtual environment, make sure that environment is activated.

## Contributors

The project has been developed under the guidance of ULI PI Dr. Yongming Liu, with student contributors 
as follows:

Hari Iyer,
PARA-ATM Founder & (Former)Lead Software Engineer,
hari.iyer@asu.edu.

Yutian Pang,
PARA-ATM Research Associate,
yutian.pang@asu.edu.
