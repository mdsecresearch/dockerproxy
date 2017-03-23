# Docker Proxy

## Introduction

Docker Proxy is a simple proof of concept for implementing a Docker container as the default browser on OS X.

## Prerequisites

In order for Docker Proxy to work correctly, it requires a number of tools to be installed:

1. Docker (https://docs.docker.com/docker-for-mac/)
2. XQuartz (https://www.xquartz.org/)
3. socat (http://www.dest-unreach.org/socat/)

Details on how to obtain and install these tools are documented below.

### Quick Start

To download and install the default Chrome image first download and install Docker.app from https://docs.docker.com/docker-for-mac/<br/>

Then run the following commands:<br/>
`brew install socat`<br/>
`brew install Caskroom/cask/xquartz`<br/>
`docker pull jess/chrome`<br/>

Download and compile the DockerProxy.app as per the github instructions.

### Installing Docker

The preferred method for using Docker with Docker Proxy is with Docker for Mac, available at https://docs.docker.com/docker-for-mac/. Instructions for installing Docker for Mac can be here; you should ensure that the default Docker machine is set to run on startup, which is the default configuration.

If however you prefer to use Docker Toolbox, you may install Docker using brew, as follows:

`brew install docker`<br/>
`brew install docker-machine`

You must then create a Docker machine using the virtualbox drivers:

`docker-machine create --driver=virtualbox default`

And start the machine:

`docker-machine start`

You can configure the default machine to launch on boot using launchctl:

`launchctl load /Applications/Docker\ Proxy.app/Contents/Resources/res/dockerproxy.plist`

## Setting Up X Forwarding

In order to receive the GUI from the Docker container, we must forward the XQuartz X11 port from the container network to the socket where it is listening.

To do this, we must first install the necessary components:<br/>
`brew install socat`<br/>
`brew install Caskroom/cask/xquartz`<br/>

Once XQuartz is installed, we must open a terminal window using `xterm`. In the newly displayed xterm window, you should run socat to forward TCP port 6000 to the correct display socket, similar to the following:

`socat TCP-LISTEN:6000,reuseaddr,fork,bind=192.168.99.1,range=192.168.99.1/24 UNIX-CLIENT:\"$DISPLAY\"`

This causes socat to bind on TCP 6000 on 192.168.99.1, our interface on the container LAN, and forward incoming connections to the display socket.

## Setting Up A Browser Image

In order to use DockerProxy, we require an image containing a browser. You may build your own hardened image or use one of the many pre-built images created by the Docker community.

For the purposes of this PoC, we'll use the Chrome image created by Jessie Frazelle (https://hub.docker.com/r/jess/chrome/) although any of the freely available images should work.

Firstly, we must obtain the image using the `docker pull jess/chrome` command.

DockerProxy is pre-configured to use this image, however if you decide to use an alternate image or build your own, you must make some changes to the "dockerproxy.py" script. Firstly, you must change the name of the image in the "DOCKER_THROWAWAYCMDARGS" variable which by default is set to "jess/chrome" as follows:

`DOCKER_THROWAWAYCMDARGS="run --rm --memory 512mb -v /etc/localtime:/etc/localtime:ro -e DISPLAY=192.168.99.1:0 -v /Users/{}/Downloads:/root/Downloads -v /dev/shm:/dev/shm --security-opt seccomp:/Applications/DockerProxy.app/Contents/Resources/res/chrome.json --group-add audio --group-add video jess/chrome --user-data-dir=/data --force-device-scale-factor=1 {}"`

You may also need to configure a custom security profile as the default Docker container profile is too restrictive to permit Chrome to construct it's sandbox. In the above example this is done using the --security-opt seccomp parameter.

## Building From Source

DockerProxy can be built from source using py2app, the following commands will retrieve the necessary modules and compile the app:

`git clone https://github.com/mdsecresearch/dockerproxy`<br/>
`cd dockerproxy`<br/>
`virtualenv venv`<br/>
`. ./venv/bin/activate`<br/>
`pip install six`<br/>
`pip install packaging`<br/>
`pip install appdirs`<br/>
`python setup.py py2app`<br/>

## Future Work

This project was created as a proof of concept to demonstrate how Docker can be integrated with the operating system to provide containers for GUI applications. Future work may include a similar concept for implementing a default handler for opening various file types such doc, PDF, xls etc in a Docker container. Additionally, the concept should be trivial to port to other operating systems. Pull requests are welcome :)
