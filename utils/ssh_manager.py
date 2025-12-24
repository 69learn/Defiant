import paramiko
import io

class SSHManager:
    def __init__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    def connect(self, hostname, port, username, password):
        try:
            self.ssh.connect(hostname, port=port, username=username, password=password, timeout=10)
            return True
        except Exception as e:
            print(f"خطا در اتصال SSH: {e}")
            return False
    
    def execute_command(self, command):
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            return output, error
        except Exception as e:
            return "", str(e)
    
    def upload_file(self, local_file, remote_file):
        try:
            sftp = self.ssh.open_sftp()
            sftp.put(local_file, remote_file)
            sftp.close()
            return True
        except Exception as e:
            print(f"خطا در آپلود فایل: {e}")
            return False
    
    def upload_string(self, content, remote_file):
        """Upload string content directly to remote file"""
        try:
            sftp = self.ssh.open_sftp()
            with sftp.file(remote_file, 'w') as f:
                f.write(content)
            sftp.close()
            return True
        except Exception as e:
            print(f"خطا در آپلود محتوا: {e}")
            return False
    
    def download_file(self, remote_file, local_file):
        """Download file from remote server"""
        try:
            sftp = self.ssh.open_sftp()
            sftp.get(remote_file, local_file)
            sftp.close()
            return True
        except Exception as e:
            print(f"خطا در دانلود فایل: {e}")
            return False
    
    def disconnect(self):
        self.ssh.close()
