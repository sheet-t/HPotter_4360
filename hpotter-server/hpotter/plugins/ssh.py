import socket
import sys
import threading
from binascii import hexlify
import paramiko
from paramiko.py3compat import u, decodebytes
import _thread

import hpotter.env
from hpotter import tables
from hpotter.env import logger, write_db, ssh_server, getLocalRemote
from hpotter.docker_shell.shell import fake_shell

class SSHServer(paramiko.ServerInterface):
    undertest = False
    data = (
        b"AAAAB3NzaC1yc2EAAAABIwAAAIEAyO4it3fHlmGZWJaGrfeHOVY7RWO3P9M7hp"
        b"fAu7jJ2d7eothvfeuoRFtJwhUmZDluRdFyhFY/hFAh76PJKGAusIqIQKlkJxMC"
        b"KDqIexkgHAfID/6mqvmnSJf0b5W8v5h2pI/stOSwTQ+pxVhwJ9ctYDhRSlF0iT"
        b"UWT10hcuO4Ks8=")
    good_pub_key = paramiko.RSAKey(data=decodebytes(data))

    def __init__(self, connection):
        self.event = threading.Event()
        self.connection = connection

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # changed so that any username/password can be used
        if username and password:
            login = tables.Credentials(username=username, password=password, \
                connection=self.connection)
            write_db(login)

            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        print("Auth attempt with key: " + u(hexlify(key.get_fingerprint())))
        if username == 'exit':
            sys.exit(1)
        if(username == "user") and (key == self.good_pub_key):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_with_mic(self, username, \
        gss_authenticated=paramiko.AUTH_FAILED, cc_file=None):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_keyex(self, username, \
        gss_authenticated=paramiko.AUTH_FAILED, cc_file=None):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    # Turned off, causing problems
    def enable_auth_gssapi(self):
        return False

    def get_allowed_auths(self, username):
        return "gssapi-keyex,gssapi-with-mic,password,publickey"

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    # pylint: disable=R0913
    def check_channel_pty_request(self, channel, term, width, height, \
        pixelwidth, pixelheight, modes):
        return True

class SshThread(threading.Thread):
    def __init__(self, address='0.0.0.0', port=22):
        super(SshThread, self).__init__()
        self.ssh_socket = socket.socket(socket.AF_INET)
        self.ssh_socket.bind((address, port))
        self.ssh_socket.listen(4)
        self.chan = None

    def run(self):
        while True:
            try:
                client, addr = self.ssh_socket.accept()
            except ConnectionAbortedError:
                break
            except OSError:
                break

            connection = tables.Connections(
                sourceIP=addr[0],
                sourcePort=addr[1],
                destPort=self.ssh_socket.getsockname()[1],
                localRemote = getLocalRemote(addr[0]),
                proto=tables.TCP)
            write_db(connection)

            transport = paramiko.Transport(client)
            transport.load_server_moduli()

            # Experiment with different key sizes at:
            # http://travistidwell.com/jsencrypt/demo/
            host_key = paramiko.RSAKey(filename="RSAKey.cfg")
            transport.add_server_key(host_key)


            server = SSHServer(connection)
            transport.start_server(server=server)

            self.chan = transport.accept()
            if not self.chan:
                logger.info('no chan')
                continue
            fake_shell(self.chan, connection, '# ')
            self.chan.close()


    def stop(self):
        #self.ssh_socket.shutdown(socket.SHUT_WR)
        self.ssh_socket.close()
        if self.chan:
            self.chan.close()
        try:
            _thread.exit()
        except SystemExit:
            pass

def start_server(address, port):
    global ssh_server
    ssh_server = SshThread(address, port)
    threading.Thread(target=ssh_server.run).start()
    logger.info("The SSH Server is up and running")

def stop_server():
    if ssh_server:
        ssh_server.stop()
        logger.info("The ssh-server was shutdown")
