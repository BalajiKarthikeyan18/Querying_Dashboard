import streamlit as st
import json
import glob
import re
import networkx as nx  # <-- Import networkx here
from functools import lru_cache
from structural_queries import ego_graph_query, node_details_query, plotly_ego_graph, retrieve_edge_attributes, find_shortest_path, get_ancestors_descendants
from product_offering_queries import query_parts_for_product_offering, query_profitable_products
# Class for handling temporal graphs
class TemporalGraph:
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

# Utility function for natural sorting of files
def natural_sort(files):
    return sorted(files, key=lambda x: int(re.search(r'timestamp_(\d+)', x).group(1)))

# Streamlit app starts here
def main():
    st.title("Temporal Graph Dashboard")

    # Specify the directory containing JSON files
    data_directory = "D:/LAM/End Card/EndCard/size_1000/"
    files = glob.glob(f"{data_directory}timestamp_*.json")

    if not files:
        st.error("No JSON files found in the specified directory.")
        return

    # Sort files naturally
    sorted_files = natural_sort(files)

    # Initialize TemporalGraph
    temporal_graph = TemporalGraph(sorted_files)

    # Load the first graph to verify successful processing
    graph = temporal_graph.load_graph_at_timestamp(0)

    # Success message
    st.success("Files processed successfully!")

    # Create tabs for queries
    st.subheader("Queries")
    tabs = st.tabs(["Structural", "Business Group", "Product Family", "Product Offering",
                    "Supplier", "Warehouse", "Facility", "Parts"])

    with tabs[0]:  # Structural Tab
        # Add markdown to select queries
        st.markdown("""
            ## Select Query to Execute :
        """)

        # Dropdown to select query
        query_type = st.selectbox("Choose Query", ["Ego Graph", "Node Details", "Edge Attributes","Shortest Path", "Ancestors and Descendants"])

        # Execute the chosen query
        if query_type == "Ego Graph":
            node_id = st.text_input("Enter Node ID for Ego Graph", "BG_001")
            radius = st.slider("Select Radius for Ego Graph", 1, 5, 2)  # Slider for radius
            # Generate the ego graph using the selected node and radius
            ego_graph = ego_graph_query(graph, node_id, radius)
            if ego_graph:
                st.write(f"Ego Graph for Node: {node_id}")
                st.write(f"Nodes: {ego_graph.number_of_nodes()}, Edges: {ego_graph.number_of_edges()}")

                # Visualize and render the ego graph with Plotly
                fig = plotly_ego_graph(ego_graph)
                st.plotly_chart(fig)  # Display the figure in Streamlit

        elif query_type == "Node Details":
            node_id = st.text_input("Enter Node ID for Node Details", "BG_001")
            node_data = node_details_query(graph, node_id)
            st.json(node_data)
        
        elif query_type == "Edge Attributes":
            node_id = st.text_input("Enter Node ID to Retrieve Edge Attributes", "BG_001")
            if node_id:
                edge_attributes = retrieve_edge_attributes(graph, node_id)
                if edge_attributes:
                    st.write(f"Edges connected to Node {node_id}:")
                    st.json(edge_attributes)
                else:
                    st.warning(f"No edges found for Node {node_id}.")
        
        elif query_type == "Shortest Path":
            source_node = st.text_input("Enter Source Node ID", "BG_001")
            destination_node = st.text_input("Enter Destination Node ID", "BG_002")

            if st.button("Find Shortest Path"):
                if source_node and destination_node:
                    path, length, fig = find_shortest_path(graph, source_node, destination_node)
                    if path and length:
                        st.write(f"Shortest Path from {source_node} to {destination_node}: {path}")
                        st.write(f"Path Length: {length}")

                # Display the visualization
                        st.plotly_chart(fig)
                    elif path is None:
                        st.warning(f"No path exists between {source_node} and {destination_node}.")
                    else:
                        st.error(f"Error: {path}")
                else:
                    st.error("Please enter valid source and destination nodes.")
        
        elif query_type == "Ancestors and Descendants":
            node_id = st.text_input("Enter Node ID to Retrieve Ancestors and Descendants", "BG_001")
            if node_id:
                try:
                    if node_id not in graph.nodes:
                        raise ValueError(f"Node '{node_id}' does not exist in the graph.")
                    ancestors, descendants = get_ancestors_descendants(graph, node_id)

                    st.subheader(f"Results for Node: {node_id}")
                    st.write(f"**Ancestors ({len(ancestors)}):**")
                    st.write(ancestors if ancestors else "No ancestors found.")
                    st.write(f"**Descendants ({len(descendants)}):**")
                    st.write(descendants if descendants else "No descendants found.")

                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")
    
    with tabs[3]:
        st.markdown("""
            ## Select Query to Execute :
        """)

        # Dropdown to select query
        query_type = st.selectbox("Choose Query", ["Parts needed to manufacture a product", "Profitable Product Offerings"])

        if query_type == "Parts needed to manufacture a product":
            product_offering_id = st.text_input("Enter Product Offering ID", "PO_001")
            if st.button("Find Parts"):
                parts = query_parts_for_product_offering(graph, product_offering_id)
                if parts:
                    st.write(f"Parts needed to manufacture {product_offering_id}:")
                    st.json(parts)
                else:
                    st.warning(f"No valid parts found for Product Offering {product_offering_id}.")

        elif query_type == "Profitable Product Offerings":
            cost_threshold = st.number_input("Enter Cost Threshold", min_value=0.0, value=100.0)
            demand_threshold = st.number_input("Enter Demand Threshold", min_value=0, value=10)

            if st.button("Find Profitable Products"):
                profitable_products = query_profitable_products(graph, cost_threshold, demand_threshold)
                if profitable_products:
                    st.write("Profitable Products:")
                    for product in profitable_products:
                        st.write(f"Product ID: {product[0]}, Cost: {product[1]}, Demand: {product[2]}")
                else:
                    st.warning("No profitable products found under the given thresholds.")


if __name__ == "__main__":
    main()
