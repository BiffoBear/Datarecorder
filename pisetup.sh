#!/bin/bash

# Pi setup script
echo 'setting up the raspi'
# Change initial password
# passwd

echo 'Update and upgrade apt-get'

sudo apt-get -y update
sudo apt-get -y upgrade

echo 'Install postgresql'

sudo apt-get -y install postgresql libpq-dev postgresql-client postgresql-client-common

echo 'Install sqlalchemy'

sudo apt-get -y install python3-sqlalchemy python-sqlalchemy-doc python3-psycopg2
echo 'Install scipy'

sudo apt-get -y install python3-scipy

echo 'Create a Python3 virtual env for Pycharm to use'

sudo apt-get -y install python3-venv
if [ -f ~/devenv/bin/activate ]
then
	echo 'The venv devenv already exists'
else
	echo 'Creating venv devenv.'
	python3 -m venv --system-site-packages ~/devenv
fi

if psql -lqt | cut -d \| -f 1 | grep -qw 'sensor_readings'
then
	echo 'The sensor_readings database exists.'
else
	echo echo 'Creating the pi role for Postgresql, enter password when requested!'
	sudo su postgres
	createuser pi -P -d -r -S
	echo 'Creating sensor_readings database.'
	createdb sensor_readings
	exit
fi
