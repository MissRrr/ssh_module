import subprocess

from ssh_connect import SSHConn
import time
import json
import sys


class SSHAuthorize():

    def __init__(self):
        self.connect_via_user = []  # [{node1:obj_connection_node1}]
        self.cluster_info = self.read_config()
        self.keys_to_add = {}
        # self.keys_to_remove = {}
        # self.authored_hosts = []  # ["node1","node2"]
        # self.all_keys = []

    def read_config(self):
        try:
            cluster_info = open(sys.path[0] + "/config.json", encoding='utf-8')
            json_dict = json.load(cluster_info)
            cluster_info.close()
            return json_dict

        except FileNotFoundError:
            with open(sys.path[0] + "/config.json", "w") as fw:
                json_dict = {
                    "Cluster": {}}
                json.dump(json_dict, fw, indent=4, separators=(',', ': '))
                return json_dict
        except json.decoder.JSONDecodeError:
            print('Failed to read configuration file.')
            sys.exit()

    def commit_data(self):
        with open(sys.path[0] + "/config.json", "w") as fw:
            json.dump(self.cluster_info, fw, indent=4, separators=(',', ': '))
        return self.cluster_info

    def update_data(self, first_key, data_key, data_value):
        self.cluster_info[first_key].update({data_key: data_value})
        return self.cluster_info[first_key]

    def update_member(self, first_key, data_key, data_value):
        self.cluster_info[first_key][data_key].update(data_value)
        return self.cluster_info[first_key]

    def delete_data(self, first_key, data_key):
        self.cluster_info[first_key].pop(data_key)
        return self.cluster_info[first_key]

    def delete_member(self, first_key, data_key, member_key):
        self.cluster_info[first_key][data_key].pop(member_key)
        return self.cluster_info[first_key]

    def cluster_is_exist(self, key, target):
        if target in self.cluster_info[key]:
            return True
        else:
            return False

    def node_is_exist(self, key, member):
        # 循环的字典为空则不会开始循环
        for data in self.cluster_info[key].values():
            if member in data.keys():
                return True
        return False

    def make_connect(self, ip, port, user, password):
        # update change self.connect_via_user or self.connect_via_key
        ssh = SSHConn(ip, port, user, password, timeout=100)
        # ssh.ssh_connect()
        self.connect_via_user.append(ssh)
        return ssh

    @staticmethod
    def get_public_key(ssh):
        # 已存在会提示是否覆盖，需要提前判断文件是否存在
        # 初始化节点ssh服务的（输入参数SSHClient连接对象，输出参数SSHClient连接对象）
        rsa_is_exist = bool(ssh.exctCMD('[ -f /root/.ssh/id_rsa.pub ] && echo True'))
        # 执行生成密钥操作
        if not rsa_is_exist:
            ssh.exctCMD('ssh-keygen -f /root/.ssh/id_rsa -N ""')
        # 要有停顿时间，不然public_key还未写入
        time.sleep(2)
        # 注意 /.ssh/config 文件
        config_is_exist = bool(ssh.exctCMD('[ -f /root/.ssh/config ] && echo True'))
        if not config_is_exist:
            ssh.exctCMD("echo -e 'StrictHostKeyChecking no\\nUserKnownHostsFile /dev/null' >> ~/.ssh/config ")
        public_key = ssh.exctCMD('cat /root/.ssh/id_rsa.pub').decode()
        return public_key

    # @staticmethod
    # def get_public_key_by_cmd(ip):
    #     p = subprocess.Popen(f'ssh "root@{ip}" "cat /root/.ssh/id_rsa.pub"', stderr=subprocess.PIPE,
    #                          stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
    #     out, err = p.communicate()
    #     publick_key = out.decode()
    #     return publick_key

    def get_map_key_by_host(self, cluster_name, ip):
        if cluster_name not in self.cluster_info['Cluster'].keys():
            return
        if ip not in self.cluster_info['Cluster'][cluster_name].keys():
            return
        return self.cluster_info['Cluster'][cluster_name][ip]

    def set_all_public_keys_by_cluster(self, cluster_name, all_public_key):
        if not all_public_key:
            return
        self.update_data('Cluster', cluster_name, all_public_key)
        self.commit_data()

    def insert_new_public_keys_by_cluster(self, cluster_name):
        if not self.keys_to_add:
            return
        self.update_member('Cluster', cluster_name, self.keys_to_add)
        self.commit_data()

    def get_map_key_node_for_cluster(self, cluster_name):
        if cluster_name not in self.cluster_info['Cluster'].keys():
            return
        return list(self.cluster_info['Cluster'][cluster_name].values())

    def convert_all_keys_by_cluster_to_string(self, cluster_name):
        str = ""
        if self.get_map_key_node_for_cluster(cluster_name):
            for pb_key in self.get_map_key_node_for_cluster(cluster_name):
                str = str + pb_key
        return str

    def convert_new_keys_by_cluster_to_string(self):
        str = ""
        for pb_key in self.keys_to_add.values():
            str = str + pb_key
        return str

    def distribute_all_keys_by_connect_via_user(self, cluster_name):
        all_public_keys = self.convert_all_keys_by_cluster_to_string(cluster_name)
        if not all_public_keys:
            return
        for obj_connection in self.connect_via_user:
            obj_connection.exctCMD(f"echo -e \'{all_public_keys}\' >> /root/.ssh/authorized_keys")

    def distribute_new_keys_to_old_node_by_add(self, cluster_name):
        old_node = [node for node in self.cluster_info['Cluster'][cluster_name].keys() if
                    node not in self.keys_to_add.keys()]
        new_public_keys = self.convert_new_keys_by_cluster_to_string()
        if not new_public_keys:
            return
        # >> 表示不覆盖　继续在下一行编辑
        # &>> 表示为追加
        for node in old_node:
            subprocess.run(f'ssh root@{node} "echo -e \'{new_public_keys}\' &>> /root/.ssh/authorized_keys"',
                           shell=True)

    def distribute_new_keys_to_old_node_by_remove(self, cluster_name):
        old_node = [node for node in self.cluster_info['Cluster'][cluster_name].keys()]
        new_public_keys = self.convert_all_keys_by_cluster_to_string(cluster_name)
        if not new_public_keys:
            return
        # > 表示覆盖以前内容
        for node in old_node:
            subprocess.run(f'ssh root@{node} "echo -e \'{new_public_keys}\' > /root/.ssh/authorized_keys"',
                           shell=True)

    def init_cluster(self, cluster_name, list_of_nodes):
        # 1, connect to all nodes.
        # 2, get all public_key from every node.
        # 3, cord keys(汇总all pbkey 放进字典插入）
        # 4, distribute all keys.
        if self.cluster_is_exist('Cluster', cluster_name):
            print('this cluster name is exist')
            sys.exit()
        for node in list_of_nodes:
            # make connection 的时候存放 ssh 对象
            ssh = self.make_connect(node[0], node[1], node[2], node[3])
            public_key = self.get_public_key(ssh)
            self.keys_to_add.update({node[0]: public_key})
        self.set_all_public_keys_by_cluster(cluster_name, self.keys_to_add)
        self.distribute_all_keys_by_connect_via_user(cluster_name)

    def cluster_add(self, cluster_name, list_of_nodes):
        # 1. connect new node
        # 2. get public_key from new node
        # 3. cord all new keys
        # 4. distribute new keys(这样可以使用echo来写）？ new node need all keys, old node need new keys
        if not self.cluster_is_exist('Cluster', cluster_name):
            print('this cluster name is not exist')
            sys.exit()
        for node in list_of_nodes:
            if self.node_is_exist('Cluster', node[0]):
                print(f'this {node[0]} is exist')
                continue
            ssh = self.make_connect(node[0], node[1], node[2], node[3])
            key = self.get_public_key(ssh)
            self.keys_to_add.update({node[0]: key})
        self.insert_new_public_keys_by_cluster(cluster_name)
        self.distribute_all_keys_by_connect_via_user(cluster_name)
        self.distribute_new_keys_to_old_node_by_add(cluster_name)

    def remove_from_cluster(self, cluster_name, list_of_nodes_ip):
        # 1. get public_key from remove node
        # 2. get other node authorized_keys info
        # 3. del this public_key
        # 4. rewrite processed str
        if not self.cluster_is_exist('Cluster', cluster_name):
            print('this cluster name is not exist')
            sys.exit()
        for node in list_of_nodes_ip:
            if not self.node_is_exist('Cluster', node):
                print(f'this {node} is not exist')
                continue
            # remove_pubulic_key = self.get_public_key_by_cmd(node)
            # self.keys_to_remove.update({node: remove_pubulic_key})
            subprocess.run(f'ssh "root@{node}" "rm /root/.ssh/authorized_keys"', shell=True)
            self.delete_member('Cluster', cluster_name, node)
        self.commit_data()
        self.distribute_new_keys_to_old_node_by_remove(cluster_name)


if __name__ == '__main__':
    node_infos = [['10.203.1.195', 22, 'root', 'password'], ['10.203.1.87', 22, 'root', 'password']]
    new_node_list = [['10.203.1.86', 22, 'root', 'password']]
    remove_list_ip = ['10.203.1.87', '10.203.1.86']
    # 初始化集群节点
    # ssh1 = SSHAuthorize()
    # ssh1.init_cluster('cluster1', node_infos)
    # 新增节点
    # ssh2 = SSHAuthorize()
    # ssh2.cluster_add('cluster1', new_node_list)
    # 移除节点
    # ssh3 = SSHAuthorize()
    # ssh3.remove_from_cluster('cluster1', remove_list_ip)
    # 新增节点
    # ssh4 = SSHAuthorize()
    # ssh4.cluster_add('cluster1', new_node_list)
