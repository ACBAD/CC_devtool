import asyncio
import os
import aioconsole
import zmq
import paramiko
from scp import SCPClient
from concurrent.futures import ThreadPoolExecutor


ssh_instances: dict[str, paramiko.SSHClient] = {}


async def update_file(local_path, remote_path, ssh_instance: paramiko.SSHClient):
    with SCPClient(ssh_instance.get_transport()) as scp:
        scp.put(local_path, remote_path)


async def update_dirs(local_dir, remote_dir, ssh_instance: paramiko.SSHClient):
    with SCPClient(ssh_instance.get_transport()) as scp:
        files = os.listdir(local_dir)
        for file in files:
            scp.put(os.path.join(local_dir, file), f'{remote_dir}/{file}')


async def zmq_server():
    zmq_context = zmq.Context()
    socket = zmq_context.socket(zmq.REP)
    socket.bind('tcp://0.0.0.0:37863')
    while True:
        with ThreadPoolExecutor() as executor:
            command = await loop.run_in_executor(executor, socket.recv_json)
        print(f'{command["type"]} request')
        if command['type'] == 'quit':
            break
        if command['type'] == 'register':
            if command['client_ip'] in ssh_instances:
                socket.send_json({'status': 'error', 'error': 'registered'})
                continue
            ssh = paramiko.SSHClient()
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(command['client_ip'], port=22, username=command['user_name'], password=command['password'])
            ssh_instances[command['client_ip']] = ssh
            socket.send_json({'status': 'ok'})
        if command['type'] == 'logout':
            ssh_instance = ssh_instances.pop(command['client_ip'], None)
            if ssh_instance:
                ssh_instance.close()
                socket.send_json({'status': 'ok'})
            else:
                socket.send_json({'status': 'error', 'error': 'not exist'})

        if command['client_ip'] not in ssh_instances:
            if command['type'] != 'logout':
                socket.send_json({'status': 'error', 'error': 'please register first'})
            continue

        if command['type'] == 'query':
            socket.send_json({'status': 'ok'})
        if command['type'] == 'update_file':
            local_path = command['local_path']
            try:
                if not os.path.exists(local_path):
                    socket.send_json({'status': 'error', 'error': 'local path does not exist'})
                    continue
                await update_file(local_path, command['remote_path'], ssh_instances[command['client_ip']])
                socket.send_json({'status': 'ok'})
            except Exception as e:
                socket.send_json({'status': 'error', 'error': str(e)})
                print(e)
        if command['type'] == 'update_dir':
            local_dir = command['local_path']
            try:
                if not os.path.exists(local_dir):
                    socket.send_json({'status': 'error', 'error': 'local path does not exist'})
                    continue
                await update_dirs(local_dir, command['remote_path'], ssh_instances[command['client_ip']])
                socket.send_json({'status': 'ok'})
            except Exception as e:
                socket.send_json({'status': 'error', 'error': str(e)})
                print(e)
    print('close')
    socket.close()
    zmq_context.term()


async def shell():
    while True:
        command = await aioconsole.ainput('cmd: ')
        if command == 'q':
            zmq_context = zmq.Context()
            socket = zmq_context.socket(zmq.REQ)
            socket.connect('tcp://127.0.0.1:37863')
            socket.send_json({'type': 'quit'})
            socket.close()
            zmq_context.term()
            for client in ssh_instances.values():
                client.close()
            break


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(shell())
    loop.run_until_complete(zmq_server())
