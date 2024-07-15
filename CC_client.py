import os
import sys
import zmq
import subprocess


defualt_update_list = ['models']  # 这里填入其他需要同步的环境文件


if len(sys.argv) < 2:
    raise IndexError('需要一个文件')

server_ip = '192.168.10.118'    # 服务器ip，修改为你的Windows主机地址
self_ip = '192.168.10.42'       # 机器自身ip，需要唯一，不能跟其他client相同
user_name = 'khadas'            # 登录机器的用户名
password = 'khadas'             # 登录机器的密码

zmq_context = zmq.Context()
socket = zmq_context.socket(zmq.REQ)
socket.connect(f"tcp://{server_ip}:37863")


def update_file(file_name):
    file_path = os.path.abspath(file_name)
    socket.send_json({'type': 'update_file',
                      'local_path': file_name,
                      'remote_path': file_path,
                      'client_ip': self_ip})
    return socket.recv_json()


def update_dir(dir_name):
    dir_path = os.path.abspath(dir_name)
    socket.send_json({'type': 'update_dir',
                      'local_path': dir_name,
                      'remote_path': dir_path,
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


proc = subprocess.Popen([sys.executable, sys.argv[1]])
proc.wait()
