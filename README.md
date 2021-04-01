# ssh_module

使用前提

节点需要开启 root 用户的 ssh 权限，在 /etc/ssh/sshd_config 里面增加一行 PermitRootLogin yes


节点需要安装 paramiko 模块

执行 py 文件时为 root 用户

使用步骤

代码调用
1.初始化集群免密登陆配置方法：init_cluster

-输入参数：集群名，集群节点列表（列表元素包括[['ip',port,'root','password'],……[])

-执行程序的节点为管理节点（管理节点与集群间节点为单侧连接，即管理节点可免密登陆到集群节点上，集群节点不可免密登陆到管理节点上）

2.新增节点方法：cluster_add

-输入参数：集群名，新增集群节点列表（列表元素包括[['ip',port,'root','password'],……[])

3.移除节点方法：remove_from_cluster

-输入参数：移除节点主机名列表（['hostname','XXX',……]

 

注意：每一个操作函数的调用不能是同一个实例对象
