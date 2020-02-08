#!/bin/bash
echo 'Update and upgrade apt-get'

sudo apt-get -y update
sudo apt-get -y upgrade

echo 'Install postgresql'

sudo apt-get -y install postgresql libpq-dev postgresql-client postgresql-client-common

echo "Install PIL packages"

sudo apt-get -y install libjpeg-dev  zlib1g-dev libfreetype6-dev liblcms1-dev
sudo apt-get -y install libopenjp2-7 libtiff5

echo "Install Python 3 venv"
if [ -f ../dr_env/bin/activate ]
then
  deactivate
	echo 'The venv devenv already exists'
else
	echo 'Creating venv devenv.'
	python3 -m venv --system-site-packages ../dr_env
fi

echo "Install Python required packages"
../dr_env/bin/pip install -r requirements.txt
echo "Setup complete"
