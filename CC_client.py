import os
import sys
from typing import Union
import zmq
import subprocess
import hashlib


defualt_update_list = ['models']  # 这里填入其他需要同步的环境文件


if len(sys.argv) < 2:
    raise IndexError('需要一个文件')

server_ip = '192.168.31.118'    # 服务器ip，修改为你的Windows主机地址
self_ip = '192.168.31.220'       # 机器自身ip，需要唯一，不能跟其他client相同
user_name = 'khadas'            # 登录机器的用户名
password = 'khadas'             # 登录机器的密码

zmq_context = zmq.Context()
socket = zmq_context.socket(zmq.REQ)
socket.connect(f"tcp://{server_ip}:37863")


def get_files_hash(files: Union[list, str]):
    hashobj = hashlib.md5()
    retval = {}

    # 如果传入的是目录路径，列出目录中的所有文件
    if isinstance(files, str):
        if not os.path.isdir(files):
            raise FileNotFoundError(f'路径 {files} 不存在或不是一个目录')
        files = [os.path.join(files, file) for file in os.listdir(files)]

    # 遍历文件列表并计算哈希值
    for file in files:
        if not os.path.isfile(file):  # 忽略非文件
            continue
        hashobj = hashlib.md5()

        # 分块读取文件，避免大文件占用过多内存
        with open(file, 'rb') as f:
            while chunk := f.read(8192):  # 每次读取 8192 字节
                hashobj.update(chunk)

        retval[os.path.basename(file)] = hashobj.hexdigest()

    return retval


def update_file(file_name):
    file_path = os.path.abspath(file_name)
    socket.send_json({'type': 'update_file',
                      'local_path': file_name,
                      'remote_path': file_path,
                      'client_ip': self_ip})
    return socket.recv_json()


def update_dir(dir_name):
    dir_path = os.path.abspath(dir_name)
    dir_file_hash = get_files_hash(dir_name)
    socket.send_json({'type': 'update_dir',
                      'local_path': dir_name,
                      'remote_path': dir_path,
                      'file_hash': dir_file_hash,
                      'client_ip': self_ip})
    return socket.recv_json()


print('-----------------------------------------------')
socket.send_json({'type': 'query', 'client_ip': self_ip})
response = socket.recv_json()
if response['status'] == 'error':
    print('Try to register instance')
    socket.send_json({'type': 'register', 'client_ip': self_ip, 'user_name': user_name, 'password': password})
    response = socket.recv_json()
    if response['status'] == 'error':
        raise NotImplementedError('注册ssh时出错')
response = update_file(sys.argv[1])
if response['status'] == 'error':
    raise IOError(response['error'])
else:
    print('Executable file updated successfully.')

for dirs in defualt_update_list:
    if os.path.isdir(dirs):
        response = update_dir(dirs)
        if response['status'] == 'error':
            raise IOError(response['error'])
        else:
            print(f'{dirs} files updated successfully.')
    else:
        response = update_file(dirs)
        if response['status'] == 'error':
            raise IOError(response['error'])
        else:
            print(f'{dirs} updated successfully.')

socket.close()
zmq_context.term()
print('All files updated.')
print('-----------------------------------------------')

try:
    proc = subprocess.Popen([sys.executable, sys.argv[1]])
    proc.wait()
except KeyboardInterrupt:
    print('kip')
