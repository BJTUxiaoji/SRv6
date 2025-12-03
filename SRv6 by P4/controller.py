"""A central controller computing and installing shortest paths.

In case of a link failure, paths are recomputed.
"""

import os
from networkx.algorithms import all_pairs_dijkstra

from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI



class Controller(object):
    """Controller for the fast rerouting exercise."""

    def __init__(self, zjbs):
        self.zj_bs= zjbs
        """Initializes the topology and data structures."""

        if not os.path.exists("topology.db"):
            print "Could not find topology object!\n"
            raise Exception

        self.topo = Topology(db="topology.db")
        print(self.topo)
        self.controllers = {}
        self.connect_to_switches()
        self.reset_states()
        #self.set_table_defaults()
        
        self.distances,self.paths = self.dijkstra()
        print(self.paths)


        self.hosts = self.topo.get_hosts()
        self.switches = self.topo.get_switches()

        self.install_local_sid_tables()
        self.install_transit_tables()
        """self.install_routing_v6_tables()"""
        """self.install_ipv6_lpm_tables()"""
        self.install_routing_v6_tables()

    def connect_to_switches(self):
        """Connects to all the switches in the topology."""
        for p4switch in self.topo.get_p4switches():
            thrift_port = self.topo.get_thrift_port(p4switch)
            self.controllers[p4switch] = SimpleSwitchAPI(thrift_port)

    def reset_states(self):
        """Resets registers, tables, etc."""
        for sw,control in self.controllers.items():
            if not self.is_srv6_switches(sw):
                continue
            control.reset_state()

    def install_local_sid_tables(self):

        for switch, control in self.controllers.items():
            if switch in self.get_srv6_switches():
                print "Installing local sid for switch '%s'." % switch
                print "=========================================\n"
                sid =  self.zj_bs[switch][1]
                control.table_add('local_sid', 'end',[str(sid)])

    def install_transit_tables(self):

        for switch, control in self.controllers.items():
            if switch in self.get_srv6_switches():
                print "Installing transit for switch '%s'." % switch
                print "=========================================\n"
                srcnode = switch
                for dstnode in self.hosts:
                    if dstnode==srcnode:
                        continue
                    path = self.get_shortest_path(srcnode , dstnode) 
                    print(srcnode,dstnode,path)
                    path_pop0 = path[1:]
                    print(path_pop0)
                    segmentlist_length = self.get_num_of_srv6SW_in(path_pop0) + 1 # 1 is the dstnode
                    if segmentlist_length <= 1:
                        continue
                    action = 'insert_segment_list_' + str(segmentlist_length)
                    param1 = [self.zj_bs[dstnode][1]]
                    param2 = []
                    for node in path_pop0:
                        if self.is_srv6_switches(node):
                            param2.append(self.zj_bs[node][1][:-4] )
                    param2.append(self.zj_bs[dstnode][1][:-4] )
                    print(param1,param2)
                    control.table_add('transit', action,param1,param2)

    def install_routing_v6_tables(self):

        for switch, control in self.controllers.items():
            if not self.is_srv6_switches(switch):
                continue
            print "Installing routing_v6 for switch '%s'." % switch
            print "=========================================\n"
            for host in self.hosts:
                path = self.get_shortest_path(switch , host)
                print "the path between {0} and {1} is {2}".format(switch,host,path) 
                next_hop = path[1]
                print "next_hop is {0}".format(next_hop)
                print "exit_port is {0}".format(str(self.get_port(switch,next_hop)))
                control.table_add('routing_v6', 'set_next_hop',[self.zj_bs[host][1]],['08:00:00:00:00:00',str(self.get_port(switch,next_hop))])
            for other_switch in self.switches:
                if other_switch == switch:
                    continue
                if not self.is_srv6_switches(other_switch):
                    continue
                path = self.get_shortest_path(switch , other_switch)
                print "the path between {0} and {1} is {2}".format(switch,other_switch,path) 
                next_hop = path[1]
                print "next_hop is {0}".format(next_hop)
                control.table_add('routing_v6', 'set_next_hop',[self.zj_bs[other_switch][1]],['08:00:00:00:00:00',str(self.get_port(switch,next_hop))])

    

    def get_srv6_switches(self):
        #L = ['s1','s2','s3','s5','s6','s7','s8']
        L = []
        for node in self.zj_bs.keys():
            if node[0]=='s':
                L.append(node)
        #print(L)
        return L

    def is_srv6_switches(self, node):
        if node in self.get_srv6_switches():
            return True
        return False

    def get_shortest_path(self,node1 ,node2):
        """todo"""
        if node1 in self.paths and node2 in self.paths[node1]:
            return self.paths[node1][node2]  # Return the path from node1 to node2
        else:
            print "can not find the path between {0} and {1}".format(node1,node2)
            return []  # If no path exists, return an empty list
        
    def get_num_of_srv6SW_in(self,path):
        """consume the number of srv6 sw"""
        num = 0
        for node in path:
            if node in self.get_srv6_switches():
                num = num+1
        return num

    def get_host_net(self, host):
        """Return ip and subnet of a host.

        Args:
            host (str): The host for which the net will be retruned.

        Returns:
            str: IP and subnet in the format "address/mask".
        """
        gateway = self.topo.get_host_gateway_name(host)
        return self.topo[host][gateway]['ip']

    def get_nexthop_index(self, host):
        """Return the nexthop index for a destination.

        Args:
            host (str): Name of destination node (host).

        Returns:
            int: nexthop index, used to look up nexthop ports.
        """
        # For now, give each host an individual nexthop id.
        host_list = sorted(list(self.topo.get_hosts().keys()))
        return host_list.index(host)

    def get_port(self, node, nexthop_node):
        """Return egress port for nexthop from the view of node.

        Args:
            node (str): Name of node for which the port is determined.
            nexthop_node (str): Name of node to reach.

        Returns:
            int: nexthop port
        """
        return self.topo.node_to_node_port_num(node, nexthop_node)


    def dijkstra(self, failures=None):
        """Compute shortest paths and distances.

        Args:
            failures (list(tuple(str, str))): List of failed links.

        Returns:
            tuple(dict, dict): First dict: distances, second: paths.
        """
        graph = self.topo.network_graph
        print(callable(self.topo.network_graph))
        print("gragh:")
        print(graph)

        if failures is not None:
            graph = graph.copy()
            for failure in failures:
                graph.remove_edge(*failure)

        # Compute the shortest paths from switches to hosts.
        dijkstra = dict(all_pairs_dijkstra(graph, weight='weight'))

        distances = {node: data[0] for node, data in dijkstra.items()}
        paths = {node: data[1] for node, data in dijkstra.items()}

        return distances, paths




if __name__ == "__main__":
    #zujian biaoshi mozu
    zjbs={'s1':['FF::1/128','A::1/128'],'s2':['FF::2','A::2/128'],'s3':['FF::3','A::3/128'],'s5':['FF::5','B::5/128'],'s6':['FF::6','B::6/128'],'s7':['FF::7','B::7/128'],'s8':['FF::8','B::8/128'],'h1':['EE::1','1::1/128'],'h2':['EE::2','2::2/128']}
    controller = Controller(zjbs)  # pylint: disable=invalid-name

    #controller_s4 = SimpleSwitchAPI('9093')

