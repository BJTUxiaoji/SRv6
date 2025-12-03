# 项目名称
基于Mininet的SRv6网络仿真与增量部署验证平台

# 项目概述
本项目通过Mininet搭建了一个混合网络仿真环境，环境包含支持SRv6的现代节点与仅支持标准IPv6的传统节点，模拟真实网络升级场景。

# 仿真拓扑
<img width="416" height="127" alt="topo" src="https://github.com/user-attachments/assets/6dbf4aea-8847-4138-b5da-180fb7407528" />

其中节点s4仅支持IPv6，不支持SRv6协议，模拟尚未升级的网络设备；其余节点均支持SRv6和IPv6转发。

# 运行环境
Ubuntu18.04

需要nsg-ethz/p4-learning

# 转发实验
1.在目录下打开一个terminal终端，运行sudo p4run，这一步将启动mininet仿真环境

2.重新打开一个新的terminal终端，运行controller.py，这一步将会通过控制器下发流表

3.使用xterm打开h1和h2终端，使用分别运行sudo python ./send.py 1::1 2::2 "hi"和sudo python ./receive.py

# 使用你的拓扑
1.修改P4app.json文件中的links

2.修改controller.py：修改main函数部分的zjbs字典值的第二项（这一项为真正使用的SID，前一项没用）


# Project Name
SRv6 Network Simulation and Incremental Deployment Verification Platform Based on Mininet

# Project Overview
This project builds a hybrid network simulation environment using Mininet. The environment includes modern nodes supporting SRv6 and traditional nodes supporting only standard IPv6, simulating real-world network upgrade scenarios.

# Simulation Topology
<img width="416" height="127" alt="topo" src="https://github.com/user-attachments/assets/6dbf4aea-8847-4138-b5da-180fb7407528" />
Among them, node s4 only supports IPv6 and does not support the SRv6 protocol, simulating a network device that has not yet been upgraded; all other nodes support both SRv6 and IPv6 forwarding.

# Runtime Environment
Ubuntu 18.04

Requires nsg-ethz/p4-learning

# Forwarding Experiment
1. Open a terminal in the directory and run sudo p4run. This step will start the Mininet simulation environment.

2. Open a new terminal and run controller.py. This step will push flow tables via the controller.

3. Use xterm to open terminals for h1 and h2. Run sudo python ./send.py 1::1 2::2 "hi" and sudo python ./receive.py respectively.

# Using Your Own Topology
1. Modify the links in the P4app.json file.

2. Modify controller.py: Change the second item in the value of the zjbs dictionary in the main function (this item is the actual SID used, the first item is unused).
