#!/bin/bash
cd
cd compass
mv prefixes.json /home/neel_satyavolu
cd
rm -rf compass
git clone https://github.com/lordfalcon787/compass-official compass
cd
mv prefixes.json /home/neel_satyavolu/compass/
cd compass
python3.12 bot.py