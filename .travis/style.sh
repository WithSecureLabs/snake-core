#!/bin/bash
set -ev

# Do the dependencies
sudo apt-get -y install python3-dev python3-pip
sudo -H pip3 install --upgrade pip setuptools
sudo python3 setup.py develop

# Run the checkers
python3 setup.py flake8
python3 setup.py lint

# Exit cleanly
exit 0
