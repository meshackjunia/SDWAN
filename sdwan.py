import networkx as nx
import random
import time
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class NetworkLink:
    latency: float  # in ms
    jitter: float   # in ms
    packet_loss: float  # percentage
    bandwidth: float    # in Mbps
    cost: float        # monetary or preference cost

@dataclass
class TrafficFlow:
    source: str
    destination: str
    required_bandwidth: float
    priority: int  # 1 (highest) to 5 (lowest)
    sensitivity: str  # 'latency', 'throughput', 'reliability'

class SDWANController:
    def __init__(self):
        self.topology = nx.Graph()
        self.flows = {}
        self.policies = []
        self.performance_metrics = {}

    def add_node(self, node_id: str, node_type: str):
        self.topology.add_node(node_id, type=node_type)

    def add_link(self, node1: str, node2: str, link: NetworkLink):
        self.topology.add_edge(node1, node2, **link.__dict__)

    def add_traffic_flow(self, flow_id: str, flow: TrafficFlow):
        self.flows[flow_id] = flow

    def update_link_metrics(self, node1: str, node2: str, **metrics):
        if self.topology.has_edge(node1, node2):
            for metric, value in metrics.items():
                self.topology[node1][node2][metric] = value

    def calculate_best_path(self, flow_id: str) -> List[str]:
        flow = self.flows[flow_id]
        if flow.sensitivity == 'latency':
            path = nx.shortest_path(self.topology, flow.source, flow.destination, weight='latency')
        elif flow.sensitivity == 'throughput':
            path = nx.shortest_path(self.topology, flow.source, flow.destination, weight=lambda u, v, d: 1/d['bandwidth'])
        elif flow.sensitivity == 'reliability':
            path = nx.shortest_path(self.topology, flow.source, flow.destination, weight=lambda u, v, d: d['packet_loss'] + d['jitter']*0.1)
        else:
            path = nx.shortest_path(self.topology, flow.source, flow.destination)
        return path

    def simulate_traffic(self):
        results = {}
        for flow_id, flow in self.flows.items():
            path = self.calculate_best_path(flow_id)
            path_metrics = self._get_path_metrics(path)
            results[flow_id] = {
                'path': path,
                'metrics': path_metrics,
                'score': self._calculate_path_score(path_metrics, flow)
            }
        return results

    def _get_path_metrics(self, path: List[str]) -> Dict:
        latency = 0
        jitter = 0
        packet_loss = 1
        bandwidth = float('inf')
        
        for i in range(len(path)-1):
            edge = self.topology[path[i]][path[i+1]]
            latency += edge['latency']
            jitter += edge['jitter']
            packet_loss *= (1 - edge['packet_loss']/100)
            bandwidth = min(bandwidth, edge['bandwidth'])
            
        return {
            'latency': latency,
            'jitter': jitter,
            'packet_loss': (1 - packet_loss) * 100,
            'bandwidth': bandwidth
        }

    def _calculate_path_score(self, metrics: Dict, flow: TrafficFlow) -> float:
        if flow.sensitivity == 'latency':
            score = 100 - metrics['latency'] * 0.5 - metrics['jitter'] * 0.3
        elif flow.sensitivity == 'throughput':
            score = metrics['bandwidth'] / flow.required_bandwidth * 100
        elif flow.sensitivity == 'reliability':
            score = 100 - metrics['packet_loss'] * 2 - metrics['jitter'] * 0.5
        return max(0, min(100, score))

class DynamicPathOptimizer:
    def __init__(self, controller: SDWANController):
        self.controller = controller
        self.history = []
        
    def monitor_links(self):
        for u, v in self.controller.topology.edges():
            new_latency = self.controller.topology[u][v]['latency'] * random.uniform(0.9, 1.1)
            new_jitter = self.controller.topology[u][v]['jitter'] * random.uniform(0.8, 1.2)
            new_loss = min(5, max(0, self.controller.topology[u][v]['packet_loss'] + random.uniform(-0.1, 0.1)))
            self.controller.update_link_metrics(u, v, latency=new_latency, jitter=new_jitter, packet_loss=new_loss)
    
    def optimize_paths(self, threshold=10):
        current_state = self._capture_state()
        if self.history:
            last_state = self.history[-1]
            if self._state_diff(last_state, current_state) > threshold:
                print("Reoptimizing paths...")
                return True
        self.history.append(current_state)
        return False
    
    def _capture_state(self):
        state = {}
        for u, v in self.controller.topology.edges():
            state[(u, v)] = {
                'latency': self.controller.topology[u][v]['latency'],
                'jitter': self.controller.topology[u][v]['jitter'],
                'packet_loss': self.controller.topology[u][v]['packet_loss']
            }
        return state
    
    def _state_diff(self, state1, state2):
        total_diff = 0
        for key in state1:
            for metric in ['latency', 'jitter', 'packet_loss']:
                total_diff += abs(state1[key][metric] - state2[key][metric])
        return total_diff

def run_simulation():
    controller = SDWANController()
    controller.add_node("HQ", "hub")
    controller.add_node("Branch1", "cpe")
    controller.add_node("Branch2", "cpe")
    controller.add_node("CloudGW", "cloud")
    
    controller.add_link("HQ", "Branch1", NetworkLink(30, 5, 0.1, 50, 1))
    controller.add_link("HQ", "Branch2", NetworkLink(40, 8, 0.2, 50, 1))
    controller.add_link("Branch1", "Branch2", NetworkLink(20, 3, 0.05, 20, 2))
    controller.add_link("Branch1", "CloudGW", NetworkLink(60, 15, 0.3, 100, 3))
    controller.add_link("Branch2", "CloudGW", NetworkLink(70, 20, 0.4, 100, 3))
    
    controller.add_traffic_flow("voip1", TrafficFlow("Branch1", "HQ", 0.5, 1, "latency"))
    controller.add_traffic_flow("backup1", TrafficFlow("Branch1", "CloudGW", 20, 4, "throughput"))
    controller.add_traffic_flow("video1", TrafficFlow("Branch2", "HQ", 5, 2, "reliability"))
    
    optimizer = DynamicPathOptimizer(controller)
    
    for step in range(10):
        print(f"\n--- Step {step} ---")
        optimizer.monitor_links()
        if optimizer.optimize_paths():
            results = controller.simulate_traffic()
            for flow_id, result in results.items():
                print(f"Flow {flow_id}: Path: {' -> '.join(result['path'])} | Score: {result['score']:.1f}")
        time.sleep(1)

if __name__ == "__main__":
    run_simulation()