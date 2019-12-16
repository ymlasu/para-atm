# NASA NAS ULI InfoFusion


## Introduction

Information fusion for real-time national air transportation system prognostics under uncertainty. This project highlights integration of two main software systems, PARA-ATM (Arizona State University), and NATS (Optimal Synthesis Inc).

## Installation

Note that [install_PARA-ATM.sh](install_PARA-ATM.sh) was originally developed to provide a single script to handle installation of Anaconda Python, dependencies, NATS, and database setup.  This script uses package management commands that are specific to the Ubuntu Linux operating system.  It is recommended to follow the instructions below instead, although new users may prefer the script as a "one-shot" setup.

In short, the steps are:
- Install Python 3
- From the `src` directory, run: `python setup.py install`

The following sections provide further details.

### Install Python

The first step is to install Python 3 on the system.

#### Ubuntu Linux

On Ubuntu 18, this can be done using:

```
sudo apt install python3
```
Note that with this installation, python commands must be issued as `python3` or `pip3`, because on Ubuntu 18, the default `python` command refers to Python 2.  An alternative is to install Python via Anaconda: https://docs.anaconda.com/anaconda/install/, which provides a local installation of Python that is separate from the one managed by the system package manager.  With a Python 3 Anaconda installation, the `python` command will refer to the Anaconda Python 3 installation (although Anaconda also provides a `python3` command that points to the same executable).

#### Windows

There are different ways to install Python on Windows.  One approach is to use Anaconda.  In particular, the "miniconda" installation provides a minimal install, to which further packages can be added as necessary: https://docs.conda.io/en/latest/miniconda.html.  With Anaconda on Windows, it is common to use the default settings that do not add Python to the system `PATH` environment variable, in which case all Python commands are then done within the special command prompt provided by Anaconda.

If the Python install will be used for other projects in addition to PARA_ATM, it is good practice to create a virtual environment so that packages needed by PARA_ATM are isolated from other Python projects.  To do this from the Anacdona prompt:

```
conda create --name para_atm python=3.7
conda activate para_atm
```

Creating the virtual environment is optional.  It is also possible to manage virtual environments using a "plain" Python installation (not Anaconda), although the commands are slightly different.

### Install PARA_ATM Python package

In the following, the `python3` command is used to explicitly refer to Python 3.  This may be necessary on some Linux systems, such as Ubuntu 18 using a system install of Python.  If using Windows with an Anaconda Python install, replace the command `python3` with `python`.

Navigate to the `src` directory and run:

```
python3 setup.py install --user
```
This command will use `pip` to automatically install necessary Python dependencies, and then it will install the PARA_ATM package.  Make sure to use the correct `python` command: if using the system version of Python 3 on Ubuntu, the command must be `python3`.  The `--user` flags instructs the installation to go into a directory that is separate from the standard system python files.  If using a virtual environment, do not include the `--user` flag.

Developers may instead want to use:

```
python3 setup.py develop --user
```
which will create a link to the source directory, so that changes can be made to the source code without needing to re-install the package.

Once installed, the package can be imported in Python using `import PARA_ATM`.  Also, a standalone command `para_atm` is created, which will launch the graphical interface in a web browser.

### Set up database (optional)

Setting up the database is optional.  Currently, the database is required for the GUI application that is launched via `para_atm app`.

To set up the database on Ubuntu, run:

```
./dbSetup.sh
```

On other operating systems, the exact commands will differ, but the general steps are the same.  Refer to operating system specific instructions for installing postgresql.

### Install NATS (optional)

Installation of NATS is optional.  Refer to the NATS [README.txt](src/NATS/README.txt).  NATS may be distributed separately in the future.

## Testing

To test the PARA_ATM installation, run the following command from the `src` directory:

```
python3 -m unittest
```

## Usage

The PARA_ATM package may be used from within Python via `import PARA_ATM`, or through the command-line interface provided by the `para_atm` command.  For help with the command-line interface, run:

```
para_atm -h
```

## Contributors

The project has been developed under the guidance of ULI PI Dr. Yongming Liu, with student contributors 
as follows:

Hari Iyer,
PARA-ATM Founder & (Former)Lead Software Engineer,
hari.iyer@asu.edu.

Yutian Pang,
PARA-ATM Research Associate,
yutian.pang@asu.edu.
