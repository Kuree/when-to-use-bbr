# the implementation is based on
# https://github.com/mininet/mininet/blob/master/examples/cluster.py
# includes some bug fixes
# heavily refactor for modern Python syntax

import mininet.node
import mininet.link
import mininet.util
import re
import os
import pwd
import subprocess


def find_user():
    return pwd.getpwuid(os.getuid())[0]


class RemoteNode(mininet.node.Node):
    _ipMatchRegex = re.compile(r'\d+\.\d+\.\d+\.\d+')
    # ssh base command
    # -q: don't print stupid diagnostic messages
    # BatchMode yes: don't ask for password
    # ForwardAgent yes: forward authentication credentials
    ssh_base = ['ssh', '-q',
                '-o', 'BatchMode=yes',
                '-o', 'ForwardAgent=yes', '-tt']

    def __init__(self, name, server='localhost', user=None, ip=None, key=None, **kwargs):
        self.server = server
        self.ip = ip if ip is not None else self.find_server_ip(server)
        self.user = user if user is not None else find_user()

        # need to ssh into the server
        if self.user and self.server != 'localhost':
            self.ssh_dest = f"{self.user}@{self.server}"
            self.ssh_cmd = ["sudo", "-E", "-u", self.user] + self.ssh_base
            if key is not None:
                # use key if provided
                self.ssh_cmd += ["-i", key]
            self.is_remote = True
        else:
            self.ssh_dest = ""
            self.ssh_cmd = []
            self.is_remote = False
        self.shell = None

        super().__init__(name, **kwargs)

        self.pid = int(self.waitOutput())

    # Command support via shell process in namespace
    def startShell(self, *args, **kwargs):
        """Start a shell process for running commands"""
        if self.is_remote:
            kwargs.update(mnopts='-c')
        print("start shell", args, kwargs)
        super().startShell(*args, **kwargs)
        # Optional split initialization
        self.sendCmd('echo $$')

    def rpopen(self, *cmd, **opts):
        """Return a Popen object on underlying server in root namespace"""
        params = {'stdin': subprocess.PIPE,
                  'stdout': subprocess.PIPE,
                  'stderr': subprocess.STDOUT,
                  'sudo': True}
        params.update(opts)
        return self._popen(*cmd, **params)

    def rcmd(self, *cmd, **opts):
        """rcmd: run a command on underlying server
           in root namespace
           args: string or list of strings
           returns: stdout and stderr"""
        popen = self.rpopen(*cmd, **opts)
        # These loops are tricky to get right.
        # Once the process exits, we can read
        # EOF twice if necessary.
        result = ''
        while True:
            poll = popen.poll()
            result += popen.stdout.read().decode("ascii")
            if poll is not None:
                break
        return result

    @staticmethod
    def _ignoreSignal():
        """Detach from process group to ignore all signals"""
        os.setpgrp()

    def _popen(self, cmd, sudo=True, tt=True, **params):
        """Spawn a process on a remote node
            cmd: remote command to run (list)
            **params: parameters to Popen()
            returns: Popen() object"""
        if isinstance(cmd, str):
            cmd = cmd.split()
        if self.is_remote:
            if sudo:
                cmd = ['sudo', '-E'] + cmd
            if tt:
                cmd = self.ssh_cmd + cmd
            else:
                # Hack: remove -tt
                sshcmd = list(self.ssh_cmd)
                sshcmd.remove('-tt')
                cmd = sshcmd + cmd
        else:
            if self.user and not sudo:
                # Drop privileges
                cmd = ['sudo', '-E', '-u', self.user] + cmd
        params.update(preexec_fn=self._ignoreSignal)
        popen = super()._popen(cmd, **params)
        return popen

    def popen(self, *args, **kwargs):
        """Override: disable -tt"""
        return super().popen(*args, tt=False, **kwargs)

    @classmethod
    def find_server_ip(cls, server):
        # First, check for an IP address
        ip_match = cls._ipMatchRegex.findall(server)
        if ip_match:
            return ip_match[0]
        # Otherwise, look up remote server
        output = mininet.util.quietRun(f'getent ahostsv4 {server}')
        ips = cls._ipMatchRegex.findall(output)
        ip = ips[0] if ips else None
        return ip


class RemoteSwitch(RemoteNode, mininet.node.OVSSwitch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = find_user()
        self.server = "localhost"


class RemoteLink(mininet.link.Link):
    """A RemoteLink is a link between nodes which may be on different servers"""

    def __init__(self, node1, node2, **kwargs):
        """Initialize a RemoteLink
           see Link() for parameters"""
        # Create links on remote node
        self.node1 = node1
        self.node2 = node2
        self.tunnel = None
        kwargs.setdefault('params1', {})
        kwargs.setdefault('params2', {})
        self.cmd = None
        super().__init__(node1, node2, **kwargs)

    def stop(self):
        """Stop this link"""
        if self.tunnel:
            self.tunnel.terminate()
            self.intf1.delete()
            self.intf2.delete()
        else:
            mininet.link.Link.stop(self)
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
            return mininet.link.Link.makeIntfPair(intfname1, intfname2, addr1, addr2,
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
        """Make a tunnel across switches on different servers"""
        # We should never try to create a tunnel to ourselves!
        # some nodes may not have server
        # And we can't ssh into this server remotely as 'localhost',
        # so try again swapping node1 and node2
        if node2.server == 'localhost':
            return self.makeTunnel(node1=node2, node2=node1,
                                   intfname1=intfname2, intfname2=intfname1,
                                   addr1=addr2, addr2=addr1)
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
        ch = tunnel.stdout.read(1).decode("ascii")
        if ch != '@':
            ch += tunnel.stdout.read().decode("ascii")
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
        """Detailed representation of link"""
        if self.tunnel:
            if self.tunnel.poll() is not None:
                status = "Tunnel EXITED %s" % self.tunnel.returncode
            else:
                status = "Tunnel Running (%s: %s)" % (
                    self.tunnel.pid, self.cmd)
        else:
            status = "OK"
        result = "%s %s" % (mininet.link.Link.status(self), status)
        return result
