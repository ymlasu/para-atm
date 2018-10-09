#!/bin/bash

dir=${PWD}

#PARA-ATM dependencies
sudo apt-get install default-jdk
sudo apt-get install wget
[ -a ./Anaconda3-2.4.0-Linux-x86_64.sh ] || wget https://repo.continuum.io/archive/Anaconda3-2.4.0-Linux-x86_64.sh
sudo chmod +x dependencies.sh
sudo ./dependencies.sh
echo "finished PARA-ATM installation, starting NATS installation"

#NATS server dependencies
cd src/NATS/Server
[ -d ./lib ] || mkdir lib
cd dependency_library
sudo chmod +x *.sh
choice="y"
if [ -d ./jasper-1.900.1 ]
then
      echo -n "reinstall jasper? [y/n] "
      read choice
fi
if [ $choice != "n" ]
then
    echo "installing jasper, detailed info in ${PWD}/install_jasper.log"
    ./install_jasper.sh &> install_jasper.log
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${PWD}../lib/jasper/lib
fi
if [ -d ./grib_api-1.11.0 ]
then
    echo -n "reinstall grib? [y/n] "
    read choice
fi
if [ $choice != "n" ]
then
    echo "installing grib, detailed info in ${PWD}/install_grib.log"
    ./install_grib.sh &> install_grib.log
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${PWD}../lib/grib_api/lib
fi
if [ -d ./hdf5-1.8.11 ]
then
    echo -n "reinstall hdf5? [y/n] "
    read choice
fi
if [ $choice != "n" ]
then
    echo "installing hdf5, detailed info in ${PWD}/install_hdf5.log"
    ./install_hdf5.sh &> install_hdf5.log
fi
echo "done installing NATS Server, starting NATS Client dependency installation"

#configure run file
cd ../
sudo chmod +x run
sudo chmod +x utility/run_nodejs.sh
sudo chmod +x utility/node-v8.11.1-linux-x64/bin/node
cd ../../../

#NATS client dependencies
which conda || export PATH="/home/${USER}/anaconda3/bin:$PATH"
conda install -c conda-forge jpype1
conda install pyqt=4

echo "done installing NATS Client, starting database setup"

export LANGUAGE=C
export LC_ALL=C
export LANG=C
export LC_TYPE=C

#set up database
sudo service postgresql restart
sudo -u postgres createuser paraatm_user
sudo -u postgres createdb paraatm
sudo -u postgres psql <<EOF
\x
alter user paraatm_user with encrypted password 'paraatm_user';
grant all privileges on database paraatm to paraatm_user;
create foreign data wrapper pgsql;
CREATE SERVER paraatm FOREIGN DATA WRAPPER pgsql OPTIONS (host 'localhost', dbname 'paraatm', port '5432');
EOF

#restore database
cp "$dir"/data/PARA_ATM_Database_Public.backup /tmp/PARA_ATM_Database_Public.backup
sudo -u postgres pg_restore -d paraatm -1 /tmp/PARA_ATM_Database_Public.backup
rm /tmp/PARA_ATM_Database_Public.backup

sed -e "s:'.*NASA_ULI_InfoFusion/src/':'$dir/src/':" "$dir"/src/PARA_ATM/Application/LaunchApp.py > tmp.txt
mv tmp.txt "$dir"/src/PARA_ATM/Application/LaunchApp.py


echo "Done installing PARA-ATM/NATS. Verify by running 'src/PARA_ATM/Application/LaunchApp.py'"
echo "If it didn't work, try the steps in the readme or email michael.hartnett@swri.org"
