# CC_devtool
适用于python的Window to Linux跨平台开发辅助工具

适合嵌入式Linux等不方便使用大型IDE远程开发功能的系统

## 特点

1. 配合alias，可实现无缝衔接运行远程文件，省却文件同步烦恼
2. 支持一对多，一台Windows主机可分发到多个Linux机器

## 使用方法

1. 将`CC_server.py`放在Windows机器项目根目录下，`CC_client.py`放在Linux机器项目根目录下
2. 在Windows机器上启动CC_server.py并常驻运行
3. 根据自己的网络环境修改CC_client.py的配置，按照文件中的注释修改即可
4. 配置client中的`defualt_update_list`项，填入同时需要同步的其他文件，支持文件和文件夹
5. 在Linux机器上执行`alias run="sudo python3 CC_client.py"`
    
    `run`可以替换成其他字符串
6. 运行`run your_script.py`