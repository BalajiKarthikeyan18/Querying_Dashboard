import json
from functools import lru_cache
import networkx as nx

class TemporalGraphClass:
    def __init__(self, files):
        self.files = files  # List of JSON file paths

    @lru_cache(maxsize=10)
    def load_graph_at_timestamp(self, timestamp):
        with open(self.files[timestamp], 'r') as f:
            data = json.load(f)
        return self._json_to_graph(data)

    def _json_to_graph(self, data):
        graph = nx.DiGraph() if data["directed"] else nx.Graph()
        for node_type, nodes in data["node_values"].items():
            for node in nodes:
                node_id = node[-1]
                node_attributes = dict(zip(data["node_types"][node_type], node))
                graph.add_node(node_id, **node_attributes)

        all_edge_types = data["relationship_types"]
        for i in data["relationship_values"]:
            if i[0] in all_edge_types:
                attributes = {}
                for j in range(len(i) - 2):
                    key = all_edge_types[i[0]][j]
                    attributes[key] = i[j]
                graph.add_edge(i[-2], i[-1], **attributes)
            else:
                graph.add_edge(i[0], i[1])

        return graph