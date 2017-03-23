# DockerProxy - a PoC app for integrating OS X with a Docker based browser
# Author: Dominic Chell (@domchell)

import sys, os, re, pipes, shlex, logging, tkMessageBox
from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser
from os.path import expanduser
from LaunchServices import LSSetDefaultHandlerForURLScheme
from LaunchServices import LSSetDefaultRoleHandlerForContentType
from LaunchServices import LSCopyDefaultHandlerForURLScheme
from LaunchServices import LSCopyDefaultRoleHandlerForContentType

class DockerProxy:

    DEBUG = False
    # Allows downloads and assumes default IP of host - may need to alter
    DOCKER_THROWAWAYCMDARGS="run --rm --memory 512mb -v /etc/localtime:/etc/localtime:ro -e DISPLAY=192.168.99.1:0 -v /Users/{}/Downloads:/root/Downloads -v /dev/shm:/dev/shm --security-opt seccomp:/Applications/DockerProxy.app/Contents/Resources/res/chrome.json --group-add audio --group-add video jess/chrome --user-data-dir=/data --force-device-scale-factor=1 {}"
    ENVIRONMENT = ""
    FIREFOXID = "org.mozilla.firefox"
    SAFARIID = "com.apple.safari"
    CHROMEID = "com.google.chrome"
    CHROMEPATH = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
    SAFARIPATH = "/Applications/Safari.app/Contents/MacOS/Safari"
    FIREFOXPATH = "/Applications/Firefox.app/Contents/MacOS/firefox"

    if DEBUG:
        logging.basicConfig(filename='/tmp/dockerproxy.log',level=logging.DEBUG)

    def __init__(self):
        logging.debug(sys.argv)
        if len(sys.argv) >1:
            logging.debug("### Received URL : " + sys.argv[1])

        if len(sys.argv)>1:
            self.url = sys.argv[1]
            self.setup_environment()
        else:
            self.url = "https://www.mdsec.co.uk"
            self.setup_environment()

    def setup_environment(self):
        if self.DEBUG:
            logging.debug("### Setting up environment")
        #Collect the environment setup to connect to the docker machine
        new_env = os.environ.copy()
        if self.DEBUG:
            logging.debug("### Present path = " + new_env['PATH'])
        #Requires VBoxManage in path (usually /usr/local/bin) - doesn't always exist in path when launched
        #from other apps
        new_env['PATH'] = '/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/X11/bin:' + new_env['PATH']
        if self.DEBUG:
            logging.debug("### Calling docker-machine")

        environment = Popen(['docker-machine', 'env'], env=new_env, shell=False, stdout=PIPE, stderr=PIPE)
        out, err = environment.communicate()

        if self.DEBUG:
            logging.debug("### Result of docker-machine: " + out)
            logging.debug("### Any errors from docker-machine: " + err)

        out = out.split("\n")
        for line in out:
            if "=" in line:
                line=line.split(" ")
                line=line[1].split("=")
                new_env[line[0]] = line[1].replace('"', '')
        self.ENVIRONMENT = new_env

    def make_default(self):
        if self.DEBUG:
            logging.debug("### Reading current browser config")

        httphandler = LSCopyDefaultHandlerForURLScheme("http")
        configpath = expanduser("~/.dockerproxy.conf")

        # If config exists, read it so we can make sure
        # dockerproxy isn't set as default
        if os.path.isfile(configpath):
            config = SafeConfigParser()
            config.read(configpath)
            httphandler = config.get('browser','httphandler')

        if "dockerproxy" not in httphandler:
            if self.DEBUG:
                logging.debug("### Writing current browser details to config file")

            # Assuming same config for all
            newconfig = SafeConfigParser()
            newconfig.add_section("browser")
            newconfig.set('browser', 'httphandler', httphandler)

            with open(configpath, 'w') as f:
                newconfig.write(f)
                f.close()

        if self.DEBUG:
            logging.debug("### Overwriting default browser")

        LSSetDefaultRoleHandlerForContentType("public.html", 0x00000002, "uk.co.mdsec.osx.dockerproxy")
        LSSetDefaultRoleHandlerForContentType("public.xhtml", 0x00000002, "uk.co.mdsec.osx.dockerproxy")
        LSSetDefaultHandlerForURLScheme("http", "uk.co.mdsec.osx.dockerproxy")
        LSSetDefaultHandlerForURLScheme("https", "uk.co.mdsec.osx.dockerproxy")
        sys.exit(0)

    def restore_config(self):
        config = SafeConfigParser()
        configpath = expanduser("~/.dockerproxy.conf")
        logging.debug("### Checking for config")
        if not os.path.isfile(configpath):
            tkMessageBox.showinfo("Error", "Config file does not exist")
            return

        config.read(configpath)
        # Assuming same for all
        httphandler = config.get('browser','httphandler')

        if self.DEBUG:
            logging.debug("### Setting original configuration")

        LSSetDefaultRoleHandlerForContentType("public.html", 0x00000002, httphandler)
        LSSetDefaultRoleHandlerForContentType("public.xhtml", 0x00000002, httphandler)
        LSSetDefaultHandlerForURLScheme("http", httphandler)
        LSSetDefaultHandlerForURLScheme("https", httphandler)

        sys.exit(0)

    def run_browser(self):
        configpath = expanduser("~/.dockerproxy.conf")
        logging.debug(configpath)
        if os.path.isfile(configpath):
            config = SafeConfigParser()
            config.read(configpath)
            httphandler = config.get('browser','httphandler')
            if "chrome" in httphandler:
                defaultbrowserpath = self.CHROMEPATH
            elif "firefox" in httphandler:
                defaultbrowserpath = self.FIREFOXPATH
            elif "safari" in httphandler:
                defaultbrowserpath = self.SAFARIPATH
            else:
                # *shrug* you're using something else
                defaultbrowserpath = self.SAFARIPATH

            #attempt to avoid cmd & arg injection
            defaultbrowserpath += " {}"
            cmd = shlex.split(defaultbrowserpath.format(pipes.quote(self.url)))

            if self.DEBUG:
                logging.debug("### Invoking: " + str(cmd))

            result = Popen(cmd, shell=False, env=self.ENVIRONMENT, stdin=None, stdout=None, stderr=None, close_fds=True, preexec_fn=os.setpgrp)
            # need to give the process a little time to load before exiting :)
            time.sleep(2)
            sys.exit(0)
        else:
            tkMessageBox.showinfo("Error", "Config file does not exist")

    def run_throwaway(self):
        import getpass
        username = getpass.getuser()
        #attempt to avoid cmd & arg injection
        self.DOCKER_THROWAWAYCMDARGS = self.DOCKER_THROWAWAYCMDARGS.format(username, pipes.quote(self.url))
        cmd = shlex.split("docker " + self.DOCKER_THROWAWAYCMDARGS)

        if self.DEBUG:
            logging.debug("### Invoking: " + str(cmd))

        result = Popen(cmd, shell=False, env=self.ENVIRONMENT, stdin=None, stdout=None, stderr=None, close_fds=True, preexec_fn=os.setpgrp)
        #need to give the process a little time to load before exiting :)
        time.sleep(5)
        sys.exit(0)

    def initialise_ui(self):
        if sys.version_info < (3, 0):
            # Python 2
            import Tkinter as tk
        else:
            # Python 3
            import tkinter as tk
        root = tk.Tk()
        root.title("Docker Proxy")
        tk.Button(root, text="Make Default Browser", command=self.make_default, width=20).pack()
        tk.Button(root, text="Restore Default Browser", command=self.restore_config, width=20).pack()
        tk.Button(root, text="Open in Browser", command=self.run_browser, width=20).pack()
        tk.Button(root, text="Open in Disposable Chrome", command=self.run_throwaway, width=20).pack()

        tk.mainloop()

def main():
    dockerproxy = DockerProxy()
    dockerproxy.initialise_ui()

if __name__ == '__main__':
    # Hack to bring to front
    # Will error but we don't care
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Docker Proxy" to true' ''')
    main()
