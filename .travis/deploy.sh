#!/bin/bash
set -ev

# Do the dependencies
sudo apt-get -y install curl
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.6 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.6.list
sudo apt-get update
sudo apt-get -y install libyaml-dev mongodb-org python3-dev python3-pip redis-server libfuzzy-dev
sudo -H pip3 install --upgrade pip setuptools

# Make sure services are running
sudo systemctl start mongod
sudo systemctl start redis

# Install Snake
sudo python3 setup.py install

# Make the OS changes
SNAKE_DIR=`python3 -c 'import imp; print(imp.find_module("snake")[1])'`
sudo useradd -r -s /sbin/nologin -d /var/cache/snake snaked
sudo mkdir -p /var/cache/snake
sudo mkdir -p /var/db/snake
sudo mkdir -p /var/log/snake
sudo mkdir -p /var/log/snake-pit
sudo cp -Rfn ${SNAKE_DIR}/data/snake /etc/snake
if [ ! -f /etc/snake/snake.conf ]; then
  sudo cp /etc/snake/snake.conf.example /etc/snake/snake.conf
fi
if [ ! -f /etc/snake/systemd/snake.conf ]; then
  sudo cp /etc/snake/systemd/snake.conf.example /etc/snake/systemd/snake.conf
fi
if [ ! -f /etc/snake/systemd/snake-pit.conf ]; then
  sudo cp /etc/snake/systemd/snake-pit.conf.example /etc/snake/systemd/snake-pit.conf
fi
sudo cp $SNAKE_DIR/data/systemd/* /etc/systemd/system
sudo chown snaked:snaked -R /etc/snake
sudo chown snaked:snaked -R /var/cache/snake
sudo chown snaked:snaked -R /var/db/snake
sudo chown snaked:snaked -R /var/log/snake
sudo chown snaked:snaked -R /var/log/snake-pit
sudo systemctl daemon-reload

# Check the install
sudo systemctl start snake-pit || true
sudo systemctl start snake || true

sleep 10

sudo systemctl status snake-pit
sudo systemctl status snake

# Exit cleanly
exit 0
