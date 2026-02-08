#!/bin/bash
set -e

apt-get update
apt-get install -y software-properties-common
add-apt-repository -y universe
apt-get update
