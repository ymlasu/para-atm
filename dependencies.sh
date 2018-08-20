#!/bin/bash

echo "Installing PARA-ATM dependencies..."

sudo chmod 777 Anaconda3-2.4.0-Linux-x86_64.sh
./Anaconda3-2.4.0-Linux-x86_64.sh
sudo apt-get install python3-pip
sudo apt-get install postgresql
sudo apt-get install pgadmin3
sudo apt-get install postgresql-contrib
. ~/.bashrc
pip3 install psycopg2-binary
pip3 install rdflib

echo "Done."
