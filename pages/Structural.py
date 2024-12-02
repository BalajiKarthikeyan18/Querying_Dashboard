import networkx as nx
import plotly.graph_objects as go
import streamlit as st


def plotly_ego_graph(ego_graph):
    """
    Visualizes the ego graph using Plotly.
    """
    pos = nx.spring_layout(ego_graph)
    edge_x = []
    edge_y = []
    for edge in ego_graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_y.append(y0)
        edge_x.append(x1)
        edge_y.append(y1)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='gray'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    hover_text = []
    for node in ego_graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        hover_text.append(f"Node {node}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=20,
            colorbar=dict(thickness=15, title="Node Connections", xanchor="left", titleside="right")
        ),
        text=hover_text,
        textposition="top center"
    )

    layout = go.Layout(
        title="Ego Graph Visualization",
        titlefont_size=16,
        showlegend=False,
        hovermode='closest',
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
        height=600,
        width=800
    )

    fig = go.Figure(data=[edge_trace, node_trace], layout=layout)
    return fig


def ego_graph_query(graph, node_id, radius):
    """
    Returns the ego graph for a specific node within a given radius.
    """
    ego_graph = nx.ego_graph(graph, node_id, radius=radius)
    return ego_graph


def node_details_query(graph, node_id):
    """
    Returns the details of a specific node in the graph.
    """
    node_data = graph.nodes[node_id]
    return node_data


def retrieve_edge_attributes(graph, node_id):
    """
    Returns all edges connected to the given node along with their attributes.
    """
    edges = []
    for neighbor in graph.neighbors(node_id):
        if graph.has_edge(node_id, neighbor):
            edge_attributes = graph.get_edge_data(node_id, neighbor)
            edges.append({
                "from": node_id,
                "to": neighbor,
                "attributes": edge_attributes
            })
    return edges


def find_shortest_path(graph, source, destination):
    """
    Finds the shortest path between source and destination nodes and visualizes the path.

    Parameters:
        graph (nx.Graph): The graph object.
        source (str/int): Source node ID.
        destination (str/int): Destination node ID.

    Returns:
        tuple: Shortest path, length, and Plotly figure.
    """
    try:
        # Find the shortest path and its length
        path = nx.shortest_path(graph, source=source, target=destination, weight="weight")
        length = nx.shortest_path_length(graph, source=source, target=destination, weight="weight")

        # Create a subgraph containing only the shortest path
        path_edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
        subgraph = nx.Graph()
        subgraph.add_edges_from(path_edges)

        # Use spring layout for the subgraph
        pos = nx.spring_layout(subgraph)

        # Extract edge data for visualization
        edge_x = []
        edge_y = []
        for edge in subgraph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.append(x0)
            edge_y.append(y0)
            edge_x.append(x1)
            edge_y.append(y1)
            edge_x.append(None)  # Separate edges
            edge_y.append(None)

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='red'),
            hoverinfo='none',
            mode='lines'
        )

        # Extract node data for visualization
        node_x = []
        node_y = []
        node_color = []
        hover_text = []
        for node in subgraph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            # Highlight nodes based on their role in the path
            if node == source:
                node_color.append('green')  # Source
                hover_text.append(f"Source Node: {node}")
            elif node == destination:
                node_color.append('blue')  # Destination
                hover_text.append(f"Destination Node: {node}")
            else:
                node_color.append('orange')  # Intermediate
                hover_text.append(f"Intermediate Node: {node}")

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            marker=dict(
                size=20,
                color=node_color,
                line=dict(width=2, color='black')
            ),
            text=[f"{node}" for node in subgraph.nodes()],  # Display node IDs
            textposition="top center"
        )

        # Create the figure
        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title="Shortest Path Visualization",
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            height=500,
            width=700
        )

        return path, length, fig

    except nx.NetworkXNoPath:
        return None, None, None
    except nx.NodeNotFound as e:
        return str(e), None, None


def get_ancestors_descendants(graph, node_id):
    if not isinstance(graph, nx.DiGraph):
        raise TypeError("The graph must be a directed graph (nx.DiGraph).")

    if node_id not in graph:
        raise ValueError(f"Node {node_id} is not in the graph.")

    # Get ancestors
    ancestors = list(nx.ancestors(graph, node_id))

    # Get descendants
    descendants = list(nx.descendants(graph, node_id))

    return ancestors, descendants


def main():

    if "temporal_graph" not in st.session_state:
        st.error("No Temporal Graph found in the session state. Please run the main script first.")
        return

    st.markdown("""
            ## Select Query to Execute :
        """)
    
    timestamp = st.select_slider("Select Timestamp", options=range(len(st.session_state.temporal_graph.files)))
    
    graph = st.session_state.temporal_graph.load_graph_at_timestamp(timestamp)

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
        destination_node = st.text_input("Enter Destination Node ID", "P_480")

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
        node_id = st.text_input("Enter Node ID to Retrieve Ancestors and Descendants", "PF_001")
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

if __name__ == "__main__":
    main()