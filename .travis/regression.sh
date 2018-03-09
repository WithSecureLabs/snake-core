#!/bin/bash
set -ev

# Do the dependencies
sudo apt-get -y install curl
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.6 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.6.list
sudo apt-get update
sudo apt-get -y install libyaml-dev mongodb-org python3-dev python3-pip redis-server libfuzzy-dev
sudo -H pip3 install --upgrade pip setuptools
sudo python3 setup.py develop

# A few of packages not dropped by develop
sudo -H pip install pytest-regtest requests git+https://github.com/kbandla/pydeep

# Prep and run the regressions
cd ../
git clone https://github.com/countercept/snake-charmer.git
cd snake-charmer
./snake_charmer.sh -l ../snake-core

# Exit cleanly
exit 0
