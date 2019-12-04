#!/bin/bash

dir=${PWD}

echo "starting database setup"

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

echo "Done setting up database. Verify by running 'bokeh serve src/PARA_ATM/Application/LaunchApp.py'"
echo "If it didn't work, try the steps in the readme or email michael.hartnett@swri.org"
