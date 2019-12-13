# NASA NAS ULI InfoFusion


## Introduction

Information fusion for real-time national air transportation system prognostics under uncertainty. This project highlights integration of two main software systems, PARA-ATM (Arizona State University), and NATS (Optimal Synthesis Inc).

## Installation

Note that [install_PARA-ATM.sh](install_PARA-ATM.sh) was originally developed to provide a single script to handle installation of Anaconda Python, dependencies, NATS, and database setup.  This script uses package management commands that are specific to the Ubuntu Linux operating system.  It is recommended to follow the instructions below instead, although new users may prefer the script as a "one-shot" setup.

### Install Python

The first step is to install Python 3 on the system.  On Ubuntu 18, this can be done using:

```
sudo apt install python3
```
Note that with this installation, python commands must be issued as `python3` or `pip3`, because on Ubuntu 18, the default `python` command refers to Python 2.  An alternative is to install Python via Anaconda: https://docs.anaconda.com/anaconda/install/, which provides a local installation of Python that is separate from the one managed by the system package manager.  With a Python 3 Anaconda installation, the `python` command will refer to the Anaconda Python 3 installation (although Anaconda also provides a `python3` command that points to the same executable).

### Install PARA_ATM Python package

Navigate to the `src` directory and run:

```
python3 setup.py install --user
```
This command will use `pip` to automatically install necessary Python dependencies, and then it will install the PARA_ATM package.  Make sure to use the correct `python` command: if using the system version of Python 3 on Ubuntu, the command must be `python3`.  The `--user` flags instructs the installation to go into a directory that is separate from the standard system python files.

Developers may instead want to use:

```
python3 setup.py develop --user
```
which will create a link to the source directory, so that changes can be made to the source code without needing to re-install the package.

Once installed, the package can be imported in Python using `import PARA_ATM`.  Also, a standalone command `para_atm` is created, which will launch the graphical interface in a web browser.

### Set up database

On Ubuntu, run:

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
