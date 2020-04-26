#!/bin/bash

# Grab the current user's uid and gid information
USER_ID=$(id -u)
GROUP_ID=$(id -g)
GROUP=$(id -ng)
DOCKER_GID=$(cut -d: -f3 < <(getent group docker))
CNAME=${USER}_$(date +%m%d_%H%m%S)

# Set the display
if [ "$(uname)" == "Darwin" ]; then
    ip=$(ifconfig en0 | grep inet | awk '$1=="inet" {print $2}')
    xhost + $ip
    xsession="-e DISPLAY=$ip:0 -v /tmp/.X11-unix:/tmp/.X11-unix"
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    # if we weren't mapping $HOME:$HOME, we would need to at least
    # map the XAUTHORITY informaiton 
    #           -e XAUTHORITY=/tmp/.Xauthority \
    #           -v $HOME/.Xauthority:/tmp/.Xauthority \
    xsession="-e DISPLAY \
              -v /tmp/.X11-unix:/tmp/.X11-unix"
else
    echo "Unsupported Platform: " $(uname)
    exit 1
fi

# Example configuration to run container that mapps in he user's identity
# along with their home directory, allowign them to run X applications and
# docker, without requring sudo
#    --device /dev/dri \
#    --device /dev/snd \

docker run --rm -it \
    $xsession \
    --net=host \
    --workdir=$(pwd) \
    --name=$CNAME \
    -e USER=$USER \
    -e USER_ID=$USER_ID \
    -e GROUP=$GROUP \
    -e GROUP_ID=$GROUP_ID \
    -e DOCKER_GID=$DOCKER_GID \
    -v $HOME:$HOME \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /etc/localtime:/etc/localtime:ro \
    thrive20/rt106-algorithm-sdk-focal:latest \
    "$@"
