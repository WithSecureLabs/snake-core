#!/bin/bash
set -ev

# Do the dependencies
sudo apt-get -y install python3-dev python3-pip
sudo -H pip3 install --upgrade pip setuptools
sudo python3 setup.py develop

# Compile the files
python3 -m compileall snake

# Exit cleanly
exit 0
