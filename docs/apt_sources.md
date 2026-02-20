# Community `apt` repository

It can happen that a `ROS` plugin seems to be not installable by `apt`. This is because some of them are not in the main repository, but in another one called `universe`. To enable it, run these commands. I am pretty sure you have to run them in each new shell when you want to install something from it.

```bash
apt-get update
apt-get install -y software-properties-common
add-apt-repository -y universe
apt-get update
```
