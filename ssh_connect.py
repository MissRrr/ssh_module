import paramiko


class SSHConn(object):

    def __init__(self, host, port, username, password, timeout):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._username = username
        self._password = password
        self.SSHConnection = None
        self._sftp = None
        self.ssh_connect()

    def _connect(self):
        try:
            objSSHClient = paramiko.SSHClient()
            objSSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            objSSHClient.connect(self._host, port=self._port,
                                 username=self._username,
                                 password=self._password,
                                 timeout=self._timeout)
#             time.sleep(1)
#             objSSHClient.exec_command("\x003")
            self.SSHConnection = objSSHClient
        except:
            pass

    # def upload(self, localpath, remotepath):
    #     def _upload():
    #         if self._sftp is None:
    #             self._sftp = self.SSHConnection.open_sftp()
    #         self._sftp.put(localpath, remotepath)
    #     try:
    #         _upload()
    #     except AttributeError as E:
    #         print(__name__, E)
    #         print('Upload Failed,Not Connect to {}'.format(self._host))
    #         return None
    #     else:
    #         print(__name__, E)
    #         print('Upload Failed ...')

    def ssh_connect(self):
        self._connect()
        if not self.SSHConnection:
            print('Connect retry for SAN switch "%s" ...' % self._host)
            self._connect()

    def exctCMD(self, command):

        def GetRusult():
            stdin, stdout, stderr = self.SSHConnection.exec_command(command)
            data = stdout.read()
            if len(data) > 0:
                # print(data.strip())
                return data
            err = stderr.read()
            if len(err) > 0:
                print('''Excute command "{}" failed on "{}" with error:
    "{}"'''.format(command, self._host, err.strip()))

        def _return(strResult):
            if strResult:
                return strResult
            # else:
            #     s.ShowErr(self.__class__.__name__,
            #               sys._getframe().f_code.co_name,
            #               'Execute Command "{}" Failed with Error:'.format(
            #                   self._host),
            #               E)

        if self.SSHConnection:
            output = _return(GetRusult())
            if output:
                return output


if __name__ == '__main__':
    ssh = SSHConn('10.203.1.86', 22, 'root', 'password', 100)
    # ssh.ssh_connect()
    print(ssh.SSHConnection is None)
    # print(ssh.exctCMD('[ -f /root/.ssh/text.txt ] && echo True'))
    ret = ssh.exctCMD('ssh-keygen -f /root/.ssh/id_rsa -N ""')
    print(ret)

