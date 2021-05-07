from signal import signal, SIGINT, SIG_IGN
from subprocess import Popen, PIPE, STDOUT
import os
from random import randrange
import sys
import re
from itertools import groupby
from operator import attrgetter
from distutils.version import StrictVersion

from mininet.node import Node, Host, OVSSwitch, Controller
from mininet.link import Link, Intf
from mininet.net import Mininet
from mininet.topo import LinearTopo
from mininet.topolib import TreeTopo
from mininet.util import quietRun, errRun, decode
from mininet.examples.clustercli import CLI
from mininet.log import setLogLevel, debug, info, error
from mininet.clean import addCleanupCallback


# pylint: disable=too-many-arguments


def findUser():
    "Try to return logged-in (usually non-root) user"
    return (
        # If we're running sudo
            os.environ.get('SUDO_USER', False) or
            # Logged-in user (if we have a tty)
            (quietRun('who am i').split() or [False])[0] or
            # Give up and return effective user
            quietRun('whoami').strip())


class ClusterCleanup(object):
    "Cleanup callback"

    inited = False
    serveruser = {}

    @classmethod
    def add(cls, server, user=''):
        "Add an entry to server: user dict"
        if not cls.inited:
            addCleanupCallback(cls.cleanup)
        if not user:
            user = findUser()
        cls.serveruser[server] = user

    @classmethod
    def cleanup(cls):
        "Clean up"
        info('*** Cleaning up cluster\n')
        for server, user in cls.serveruser.items():
            if server == 'localhost':
                # Handled by mininet.clean.cleanup()
                continue
            else:
                cmd = ['su', user, '-c',
                       'ssh %s@%s sudo mn -c' % (user, server)]
                info(cmd, '\n')
                info(quietRun(cmd))


# BL note: so little code is required for remote nodes,
# we will probably just want to update the main Node()
# class to enable it for remote access! However, there
# are a large number of potential failure conditions with
# remote nodes which we may want to detect and handle.
# Another interesting point is that we could put everything
# in a mix-in class and easily add cluster mode to 2.0.

class RemoteMixin(object):
    "A mix-in class to turn local nodes into remote nodes"

    # ssh base command
    # -q: don't print stupid diagnostic messages
    # BatchMode yes: don't ask for password
    # ForwardAgent yes: forward authentication credentials
    sshbase = ['ssh', '-q',
               '-o', 'BatchMode=yes',
               '-o', 'ForwardAgent=yes', '-tt']

    def __init__(self, name, server='localhost', user=None, serverIP=None,
                 controlPath=False, splitInit=False, **kwargs):
        """Instantiate a remote node
           name: name of remote node
           server: remote server (optional)
           user: user on remote server (optional)
           controlPath: specify shared ssh control path (optional)
           splitInit: split initialization?
           **kwargs: see Node()"""
        # We connect to servers by IP address
        self.server = server if server else 'localhost'
        self.serverIP = (serverIP if serverIP
                         else self.findServerIP(self.server))
        self.user = user if user else findUser()
        ClusterCleanup.add(server=server, user=user)
        if controlPath is True:
            # Set a default control path for shared SSH connections
            controlPath = '/tmp/mn-%r@%h:%p'
        self.controlPath = controlPath
        self.splitInit = splitInit
        if self.user and self.server != 'localhost':
            self.dest = '%s@%s' % (self.user, self.serverIP)
            self.sshcmd = ['sudo', '-E', '-u', self.user] + self.sshbase
            if self.controlPath:
                self.sshcmd += ['-o', 'ControlPath=' + self.controlPath,
                                '-o', 'ControlMaster=auto',
                                '-o', 'ControlPersist=' + '1']
            self.sshcmd += [self.dest]
            self.isRemote = True
        else:
            self.dest = None
            self.sshcmd = []
            self.isRemote = False
        # Satisfy pylint
        self.shell, self.pid = None, None
        super(RemoteMixin, self).__init__(name, **kwargs)

    # Determine IP address of local host
    _ipMatchRegex = re.compile(r'\d+\.\d+\.\d+\.\d+')

    @classmethod
    def findServerIP(cls, server):
        "Return our server's IP address"
        # First, check for an IP address
        ipmatch = cls._ipMatchRegex.findall(server)
        if ipmatch:
            return ipmatch[0]
        # Otherwise, look up remote server
        output = quietRun('getent ahostsv4 %s' % server)
        ips = cls._ipMatchRegex.findall(output)
        ip = ips[0] if ips else None
        return ip

    # Command support via shell process in namespace
    def startShell(self, *args, **kwargs):
        "Start a shell process for running commands"
        if self.isRemote:
            kwargs.update(mnopts='-c')
        super(RemoteMixin, self).startShell(*args, **kwargs)
        # Optional split initialization
        self.sendCmd('echo $$')
        if not self.splitInit:
            self.finishInit()

    def finishInit(self):
        "Wait for split initialization to complete"
        self.pid = int(self.waitOutput())

    def rpopen(self, *cmd, **opts):
        "Return a Popen object on underlying server in root namespace"
        params = {'stdin': PIPE,
                  'stdout': PIPE,
                  'stderr': STDOUT,
                  'sudo': True}
        params.update(opts)
        return self._popen(*cmd, **params)

    def rcmd(self, *cmd, **opts):
        """rcmd: run a command on underlying server
           in root namespace
           args: string or list of strings
           returns: stdout and stderr"""
        popen = self.rpopen(*cmd, **opts)
        # info( 'RCMD: POPEN:', popen, '\n' )
        # These loops are tricky to get right.
        # Once the process exits, we can read
        # EOF twice if necessary.
        result = ''
        while True:
            poll = popen.poll()
            result += decode(popen.stdout.read())
            if poll is not None:
                break
        return result

    @staticmethod
    def _ignoreSignal():
        "Detach from process group to ignore all signals"
        os.setpgrp()

    def _popen(self, cmd, sudo=True, tt=True, **params):
        """Spawn a process on a remote node
            cmd: remote command to run (list)
            **params: parameters to Popen()
            returns: Popen() object"""
        if isinstance(cmd, str):
            cmd = cmd.split()
        if self.isRemote:
            if sudo:
                cmd = ['sudo', '-E'] + cmd
            if tt:
                cmd = self.sshcmd + cmd
            else:
                # Hack: remove -tt
                sshcmd = list(self.sshcmd)
                sshcmd.remove('-tt')
                cmd = sshcmd + cmd
        else:
            if self.user and not sudo:
                # Drop privileges
                cmd = ['sudo', '-E', '-u', self.user] + cmd
        params.update(preexec_fn=self._ignoreSignal)
        debug('_popen', cmd, '\n')
        popen = super(RemoteMixin, self)._popen(cmd, **params)
        return popen

    def popen(self, *args, **kwargs):
        "Override: disable -tt"
        return super(RemoteMixin, self).popen(*args, tt=False, **kwargs)

    def addIntf(self, *args, **kwargs):
        "Override: use RemoteLink.moveIntf"
        # kwargs.update( moveIntfFn=RemoteLink.moveIntf )
        # pylint: disable=useless-super-delegation
        return super(RemoteMixin, self).addIntf(*args, **kwargs)


class RemoteNode(RemoteMixin, Node):
    "A node on a remote server"
    pass


class RemoteHost(RemoteNode):
    "A RemoteHost is simply a RemoteNode"
    pass


class RemoteOVSSwitch(RemoteMixin, OVSSwitch):
    "Remote instance of Open vSwitch"

    OVSVersions = {}

    def __init__(self, *args, **kwargs):
        # No batch startup yet
        kwargs.update(batch=True)
        super(RemoteOVSSwitch, self).__init__(*args, **kwargs)

    def isOldOVS(self):
        "Is remote switch using an old OVS version?"
        cls = type(self)
        if self.server not in cls.OVSVersions:
            # pylint: disable=not-callable
            vers = self.cmd('ovs-vsctl --version')
            # pylint: enable=not-callable
            cls.OVSVersions[self.server] = re.findall(
                r'\d+\.\d+', vers)[0]
        return (StrictVersion(cls.OVSVersions[self.server]) <
                StrictVersion('1.10'))

    @classmethod
    # pylint: disable=arguments-differ
    def batchStartup(cls, switches, **_kwargs):
        "Start up switches in per-server batches"
        key = attrgetter('server')
        for server, switchGroup in groupby(sorted(switches, key=key), key):
            info('(%s)' % server)
            group = tuple(switchGroup)
            switch = group[0]
            OVSSwitch.batchStartup(group, run=switch.cmd)
        return switches

    @classmethod
    # pylint: disable=arguments-differ
    def batchShutdown(cls, switches, **_kwargs):
        "Stop switches in per-server batches"
        key = attrgetter('server')
        for server, switchGroup in groupby(sorted(switches, key=key), key):
            info('(%s)' % server)
            group = tuple(switchGroup)
            switch = group[0]
            OVSSwitch.batchShutdown(group, run=switch.rcmd)
        return switches


class RemoteLink(Link):
    "A RemoteLink is a link between nodes which may be on different servers"

    def __init__(self, node1, node2, **kwargs):
        """Initialize a RemoteLink
           see Link() for parameters"""
        # Create links on remote node
        self.node1 = node1
        self.node2 = node2
        self.tunnel = None
        kwargs.setdefault('params1', {})
        kwargs.setdefault('params2', {})
        self.cmd = None  # satisfy pylint
        Link.__init__(self, node1, node2, **kwargs)

    def stop(self):
        "Stop this link"
        if self.tunnel:
            self.tunnel.terminate()
            self.intf1.delete()
            self.intf2.delete()
        else:
            Link.stop(self)
        self.tunnel = None

    def makeIntfPair(self, intfname1, intfname2, addr1=None, addr2=None,
                     node1=None, node2=None, deleteIntfs=True):
        """Create pair of interfaces
            intfname1: name of interface 1
            intfname2: name of interface 2
            (override this method [and possibly delete()]
            to change link type)"""
        node1 = self.node1 if node1 is None else node1
        node2 = self.node2 if node2 is None else node2
        server1 = getattr(node1, 'server', 'localhost')
        server2 = getattr(node2, 'server', 'localhost')
        if server1 == server2:
            # Link within same server
            return Link.makeIntfPair(intfname1, intfname2, addr1, addr2,
                                     node1, node2, deleteIntfs=deleteIntfs)
        # Otherwise, make a tunnel
        self.tunnel = self.makeTunnel(node1, node2, intfname1, intfname2,
                                      addr1, addr2)
        return self.tunnel

    @staticmethod
    def moveIntf(intf, node):
        """Move remote interface from root ns to node
            intf: string, interface
            dstNode: destination Node
            srcNode: source Node or None (default) for root ns"""
        intf = str(intf)
        cmd = 'ip link set %s netns %s' % (intf, node.pid)
        result = node.rcmd(cmd)
        if result:
            raise Exception('error executing command %s' % cmd)
        return True

    def makeTunnel(self, node1, node2, intfname1, intfname2,
                   addr1=None, addr2=None):
        "Make a tunnel across switches on different servers"
        # We should never try to create a tunnel to ourselves!
        assert node1.server != node2.server
        # And we can't ssh into this server remotely as 'localhost',
        # so try again swappping node1 and node2
        if node2.server == 'localhost':
            return self.makeTunnel(node1=node2, node2=node1,
                                   intfname1=intfname2, intfname2=intfname1,
                                   addr1=addr2, addr2=addr1)
        debug('\n*** Make SSH tunnel ' + node1.server + ':' + intfname1 +
              ' == ' + node2.server + ':' + intfname2)
        # 1. Create tap interfaces
        for node in node1, node2:
            # For now we are hard-wiring tap9, which we will rename
            cmd = 'ip tuntap add dev tap9 mode tap user ' + node.user
            result = node.rcmd(cmd)
            if result:
                raise Exception('error creating tap9 on %s: %s' %
                                (node, result))
        # 2. Create ssh tunnel between tap interfaces
        # -n: close stdin
        dest = '%s@%s' % (node2.user, node2.serverIP)
        cmd = ['ssh', '-n', '-o', 'Tunnel=Ethernet', '-w', '9:9',
               dest, 'echo @']
        self.cmd = cmd
        tunnel = node1.rpopen(cmd, sudo=False)
        # When we receive the character '@', it means that our
        # tunnel should be set up
        debug('Waiting for tunnel to come up...\n')
        ch = decode(tunnel.stdout.read(1))
        if ch != '@':
            ch += decode(tunnel.stdout.read())
            cmd = ' '.join(cmd)
            raise Exception('makeTunnel:\n'
                            'Tunnel setup failed for '
                            '%s:%s' % (node1, node1.dest) + ' to '
                                                            '%s:%s\n' % (node2, node2.dest) +
                            'command was: %s' % cmd + '\n' +
                            'result was: ' + ch)
        # 3. Move interfaces if necessary
        for node in node1, node2:
            if not self.moveIntf('tap9', node):
                raise Exception('interface move failed on node %s' % node)
        # 4. Rename tap interfaces to desired names
        for node, intf, addr in ((node1, intfname1, addr1),
                                 (node2, intfname2, addr2)):
            if not addr:
                result = node.cmd('ip link set tap9 name', intf)
            else:
                result = node.cmd('ip link set tap9 name', intf,
                                  'address', addr)
            if result:
                raise Exception('error renaming %s: %s' % (intf, result))
        return tunnel

    def status(self):
        "Detailed representation of link"
        if self.tunnel:
            if self.tunnel.poll() is not None:
                status = "Tunnel EXITED %s" % self.tunnel.returncode
            else:
                status = "Tunnel Running (%s: %s)" % (
                    self.tunnel.pid, self.cmd)
        else:
            status = "OK"
        result = "%s %s" % (Link.status(self), status)
        return result


class RemoteSSHLink(RemoteLink):
    "Remote link using SSH tunnels"

    def __init__(self, node1, node2, **kwargs):
        RemoteLink.__init__(self, node1, node2, **kwargs)
