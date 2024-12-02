import streamlit as st
import json
import functools
import time
import tracemalloc
import plotly.graph_objects as go
import base64
import numpy as np
# supplier, parts
# warehouse, facility , po

def time_and_memory(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Start tracking memory and time
        tracemalloc.start()
        start_time = time.time()  # Ensure time module is used correctly

        try:
            # Call the actual function
            result = func(*args, **kwargs)
        finally:
            # Calculate memory and time usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            end_time = time.time()
            elapsed_time = end_time - start_time

            # Print results
            st.write(f"**Function Name:** `{func.__name__}`")
            st.write(f"**Time Taken:** `{elapsed_time:.2f} seconds`")
            st.write(
                f"**Memory Usage:** `{current / 1024:.2f} KiB` (Current), `{peak / 1024:.2f} KiB` (Peak)")

        return result
    return wrapper


# The @time_and_memory decorator is assumed to be pre-defined
@time_and_memory
def track_attribute_propagation(node_type, attribute, propagation_node_type=None, relationship_type=None):
    """
    Track the propagation of an attribute value over time and across related nodes.
    
    Parameters:
        node_type (str): The type of the starting node (e.g., 'Warehouse').
        attribute (str): The attribute to track (e.g., 'max_capacity').
        propagation_node_type (str): The type of the related node that should be influenced (e.g., 'Parts').
        relationship_type (str): The type of the relationship connecting the nodes (e.g., 'FacilityToProductOfferings').
    
    Returns:
        None: Displays a plot in Streamlit showing the propagation of the attribute over time.
    """
    timestamps = []
    attribute_values = []

    # Iterate over all timestamps in the temporal graph
    for timestamp in range(len(st.session_state.temporal_graph.files)):
        with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
            data = json.load(f)
        # Find the nodes of the given type and attribute at this timestamp
        if node_type in data["node_values"]:
    
            # Extract the values of the specified attribute for nodes of the given type
            nodes = data["node_values"][node_type]
            for node in nodes:
                if attribute in data["node_types"][node_type]:
                    node_value = node[data["node_types"][node_type].index(attribute)]
                    # Check for propagation to other nodes if specified
                    if propagation_node_type and relationship_type:
                        for edge in data.get("link_values", []):
                            if edge[0] == relationship_type and edge[1] == node[0]:  # Check relationship type and node
                                # For simplicity, this assumes propagation is direct and one-to-one
                                # Can be extended with more complex graph traversal
                                propagate_value = edge[2]  # Example: Use a specific relationship attribute
                                attribute_values.append(propagate_value)
                    else:
                        attribute_values.append(node_value)
            
            timestamps.append(timestamp)

    # Create a Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=attribute_values,
        mode='lines+markers',
        name=f"{attribute.capitalize()} Propagation",
        line=dict(color='red'),
        marker=dict(size=8)
    ))

    # Update layout
    fig.update_layout(
        title=f"Propagation of '{attribute}' for Node Type '{node_type}' Over Time",
        xaxis_title="Timestamps",
        yaxis_title=attribute.capitalize(),
        xaxis=dict(tickmode='linear', tick0=0, dtick=1),
        template="plotly_white",
        showlegend=True,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # Display the figure in Streamlit
    st.plotly_chart(fig, use_container_width=True)

@time_and_memory
def detect_peak_and_off_peak_periods(node_type, attribute, threshold=0.9):
    """
    Detect peak and off-peak periods based on a specific attribute (e.g., 'max_capacity') for nodes of a given type.
    
    Parameters:
        node_type (str): The type of the node to track (e.g., 'Facility').
        attribute (str): The attribute to track (e.g., 'max_capacity').
        threshold (float): The utilization threshold to identify peak periods. Default is 0.9 (90% utilization).
    """
    # Store timestamps and attribute values
    timestamps = []
    attribute_values = []
    peak_periods = []
    off_peak_periods = []
    
    # Iterate over all timestamps in the temporal graph
    for timestamp in range(len(st.session_state.temporal_graph.files)):
        # Load the data for the current timestamp
        with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
            data = json.load(f)
        
        # Check if the node type exists in the data
        if node_type in data["node_values"]:
            # Extract attribute values for all nodes of the given type
            values = [
                node[data["node_types"][node_type].index(attribute)]
                for node in data["node_values"][node_type]
                if attribute in data["node_types"][node_type]
            ]
            
            # Aggregate the attribute values (e.g., average)
            if values:
                avg_value = sum(values) / len(values)
                timestamps.append(timestamp)  # Use 0-based timestamp indexing
                attribute_values.append(avg_value)  # Store the average value of the attribute
                
                # Identify peak or off-peak periods based on the threshold
                if avg_value >= threshold:
                    peak_periods.append(timestamp)
                else:
                    off_peak_periods.append(timestamp)
    
    # Create a Plotly figure to visualize the attribute trends
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=attribute_values,
        mode='lines+markers',
        name=f"{attribute.capitalize()} Trend",
        line=dict(color='blue'),
        marker=dict(size=8)
    ))
    
    # Add vertical lines for peak and off-peak periods
    for peak in peak_periods:
        fig.add_vline(x=peak, line=dict(color='red', dash='dot'), name='Peak Period')

    for off_peak in off_peak_periods:
        fig.add_vline(x=off_peak, line=dict(color='green', dash='dot'), name='Off-Peak Period')

    # Update layout
    fig.update_layout(
        title=f"Peak and Off-Peak Periods for '{attribute}' of Node Type '{node_type}'",
        xaxis_title="Timestamps",
        yaxis_title=attribute.capitalize(),
        xaxis=dict(tickmode='linear', tick0=0, dtick=1),  # Ensure integer x-axis ticks
        template="plotly_white",
        showlegend=True,
        margin=dict(l=40, r=40, t=60, b=40)  # Adjust margins for Streamlit layout
    )

    # Display the figure in Streamlit
    st.plotly_chart(fig, use_container_width=True)
@time_and_memory
def track_attribute_over_time( node_type, attribute):

    # Store timestamp and aggregated attribute values
    timestamps = []
    attribute_values = []

    # Iterate over all timestamps in the temporal graph
    for timestamp in range(len(st.session_state.temporal_graph.files)):
        # Load the data for the current timestamp
        with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
            data = json.load(f)
        
        # Check if the node type exists in the data
        if node_type in data["node_values"]:
            # Extract attribute values for all nodes of the given type
            values = [
                node[data["node_types"][node_type].index(attribute)]
                for node in data["node_values"][node_type]
                if attribute in data["node_types"][node_type]
            ]
            # Aggregate the attribute values (e.g., average)
            if values:
                timestamps.append(timestamp)  # Use 0-based timestamp indexing
                attribute_values.append(sum(values) / len(values))  # Example: Average value

    # Create a Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=attribute_values,
        mode='lines+markers',
        name=f"{attribute.capitalize()} Trend",
        line=dict(color='blue'),
        marker=dict(size=8)
    ))

    # Update layout
    fig.update_layout(
        title=f"Trend of '{attribute}' for Node Type '{node_type}' Over Time",
        xaxis_title="Timestamps",
        yaxis_title=attribute.capitalize(),
        xaxis=dict(tickmode='linear', tick0=0, dtick=1),  # Ensure integer x-axis ticks
        template="plotly_white",
        showlegend=True,
        margin=dict(l=40, r=40, t=60, b=40)  # Adjust margins for Streamlit layout
    )

    # Display the figure in Streamlit
    st.plotly_chart(fig, use_container_width=True)


@time_and_memory
def plot_attribute_for_node_streamlit(node_id, attribute):
    # Store timestamps and attribute values
    timestamps = []
    attribute_values = []
    
    # Flag to check if the attribute is present at least once
    attribute_found = False

    # Iterate over all timestamps in the temporal graph
    for timestamp in range(len(st.session_state.temporal_graph.files)):
        # Load the data for the current timestamp
        with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
            data = json.load(f)

        # Check if the node ID exists in the data
        for node_type, nodes in data["node_values"].items():
            for subnode in nodes:
                if node_id in subnode:
                    node_index = nodes.index(subnode)
                    node_attributes = data["node_types"][node_type]

                    # Check if the attribute exists for this node type
                    if attribute in node_attributes:
                        attribute_found = True
                        value = data["node_values"][node_type][node_index][node_attributes.index(attribute)]
                        timestamps.append(timestamp)  # Use 0-based timestamp indexing
                        attribute_values.append(value)
                    break  # Exit the loop if the node is found

    if not attribute_found:
        st.error(f"Attribute '{attribute}' not found for node ID '{node_id}' in any timestamp.")
        return

    # Plot the results using Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=attribute_values,
        mode='lines+markers',
        name=f"{attribute.capitalize()} Trend",
        line=dict(color='green'),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title=f"Trend of '{attribute}' for Node ID '{node_id}' Over Time",
        xaxis_title="Timestamps",
        yaxis_title=attribute.capitalize(),
        xaxis=dict(tickmode='linear', tick0=0, dtick=1),
        template="plotly_white"
    )

    # Render the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)

@time_and_memory
def track_edge_attribute_over_time_streamlit(edge_type, attribute):
    
    # Store timestamp and aggregated attribute values
    timestamps = []
    attribute_values = []
    
    # Iterate over all timestamps in the temporal graph
    for timestamp in range(len(st.session_state.temporal_graph.files)):
        # Load the data for the current timestamp
        with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
            data = json.load(f)
        
        # Check if the edge type exists in the data
        if edge_type in data["relationship_types"]:
            # Extract attribute values for all edges of the given type
            values = [
                edge[data["relationship_types"][edge_type].index(attribute)]
                for edge in data["relationship_values"]
                if edge[0] == edge_type and attribute in data["relationship_types"][edge_type]
            ]
            # Aggregate the attribute values (e.g., average)
            if values:
                timestamps.append(timestamp)  # Use 0-based timestamp indexing
                attribute_values.append(sum(values) / len(values))  # Example: Average value
    
    if not timestamps:
        st.error(f"No data found for edge type '{edge_type}' with attribute '{attribute}' across the timestamps.")
        return
    
    # Plot the results using Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=attribute_values,
        mode='lines+markers',
        line=dict(color='green'),
        marker=dict(size=8),
        name=f"{attribute}"
    ))
    
    fig.update_layout(
        title=f"Trend of '{attribute}' for Edge Type '{edge_type}' Over Time",
        xaxis_title="Timestamps",
        yaxis_title=attribute.capitalize(),
        xaxis=dict(tickmode='linear'),  # Ensure integer timestamps on x-axis
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)



@time_and_memory
def detect_anomalies(node_type, attribute, z_threshold=1.1):
    """
    Detect anomalies in an attribute (e.g., 'operating_cost') by identifying periods where 
    the attribute deviates significantly from its mean (based on z-score).
    
    Parameters:
        node_type (str): The type of node to track (e.g., 'Facility').
        attribute (str): The attribute to track (e.g., 'operating_cost').
        z_threshold (float): The z-score threshold to detect anomalies. Default is 3 (standard deviation).
    """
    timestamps = []
    attribute_values = []

    # Collect attribute values for all timestamps
    for timestamp in range(len(st.session_state.temporal_graph.files)):
        with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
            data = json.load(f)
        
        if node_type in data["node_values"]:
            values = [
                node[data["node_types"][node_type].index(attribute)]
                for node in data["node_values"][node_type]
                if attribute in data["node_types"][node_type]
            ]
            
            if values:
                avg_value = sum(values) / len(values)
                timestamps.append(timestamp)
                attribute_values.append(avg_value)

    # Compute the z-scores for anomaly detection
    mean_value = np.mean(attribute_values)
    std_dev = np.std(attribute_values)
    z_scores = [(val - mean_value) / std_dev for val in attribute_values]

    # Identify anomalies based on z-score threshold
    anomalies = [i for i, score in enumerate(z_scores) if abs(score) > z_threshold]

    # Create a Plotly figure
    fig = go.Figure()

    # Plot the attribute values as a line plot
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=attribute_values,
        mode='lines+markers',
        name=f"{attribute.capitalize()} Trend",
        line=dict(color='blue'),
        marker=dict(size=8)
    ))

    # Highlight anomalies with distinct markers
    fig.add_trace(go.Scatter(
        x=[timestamps[i] for i in anomalies],
        y=[attribute_values[i] for i in anomalies],
        mode='markers',
        name='Anomalies',
        marker=dict(color='red', size=10, symbol='x')
    ))

    # Add expected value range as a shaded region (1 standard deviation)
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=[mean_value + std_dev] * len(timestamps),
        mode='lines',
        name='Upper Bound (1 SD)',
        line=dict(color='green', dash='dash')
    ))

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=[mean_value - std_dev] * len(timestamps),
        mode='lines',
        name='Lower Bound (1 SD)',
        line=dict(color='green', dash='dash')
    ))

    # Update layout with title and axis labels
    fig.update_layout(
        title=f"Anomalies in '{attribute}' for Node Type '{node_type}'",
        xaxis_title="Timestamps",
        yaxis_title=attribute.capitalize(),
        xaxis=dict(tickmode='linear', tick0=0, dtick=1),
        template="plotly_white",
        showlegend=True,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # Display the figure in Streamlit
    st.plotly_chart(fig, use_container_width=True)
 
def main():

    if "temporal_graph" not in st.session_state:
        st.error("No Temporal Graph found in the session state. Please run the main script first.")
        return
    
    graph = st.session_state.temporal_graph.load_graph_at_timestamp(0)
    # with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
    #     json_graph = json.load(f)

    all_id={"Supplier":[],"Warehouse":[],"ProductOffering":[],"Parts":[],"BusinessGroup":[],"ProductFamily":[],"Facility":[]}

    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("node_type") == "Supplier":
            all_id["Supplier"].append(node_id)
        elif node_data.get("node_type") == "Warehouse":
            all_id["Warehouse"].append(node_id)
        elif node_data.get("node_type") == "ProductOffering":
            all_id["ProductOffering"].append(node_id)
        elif node_data.get("node_type") == "Parts":
            all_id["Parts"].append(node_id)
        elif node_data.get("node_type") == "BusinessGroup":
            all_id["BusinessGroup"].append(node_id)
        elif node_data.get("node_type") == "ProductFamily":
            all_id["ProductFamily"].append(node_id)
        elif node_data.get("node_type") == "Facility":
            all_id["Facility"].append(node_id)




    node_data= {
    "BusinessGroup": [
      "revenue",
    ],
    "ProductFamily": [
      "revenue",
    ],
    "ProductOffering": [
      "cost",
      "demand",
    ],
    "Supplier": [
      "reliability",
      "size",
    ],
    "Warehouse": [
      "max_capacity",
      "current_capacity",
      "safety_stock",
      "max_parts",
    ],
    "Facility": [
      "max_capacity",
      "operating_cost",
    ],
    "Parts": [
      "cost",
      "importance_factor",
    ]
    }
    
    edge_data={
    "SupplierToWarehouse": [
      "transportation_cost",
      "lead_time",
    ],
    "WarehouseToParts": [
      "inventory_level",
      "storage_cost",
    ],
    "PartsToFacility": [
      "quantity",
      "distance",
      "transport_cost",
      "lead_time",
    ],
    "FacilityToParts": [
      "production_cost",
      "lead_time",
      "quantity",
    ],
    "FacilityToProductOfferings": [
      "product_cost",
      "lead_time",
      "quantity",
    ],
    }

    st.title("Querying Across Timestamps")

    queries = ["Select",
            "Plot average of a node attribute over timestamps.",
            "Plot attribute of a Node id over timestamps.",
            "Plot average of an edge attribute over timestamps.",
            "Anomaly Detection in Attributes."
               ]
    query = st.selectbox("Choose Query", queries)
    

    if query == "Plot average of a node attribute over timestamps.":
        st.write("This query generates a plot of the average value of a node attribute over timestamps, providing insights into the temporal trend of the attribute.")
        node_type = st.selectbox("Select Node Type:", options=node_data.keys())
        attribute = st.selectbox("Select Node Attribute:", options=node_data[node_type])
        if st.button("Plot Trend"):
            track_attribute_over_time(node_type, attribute)
            # track_attribute_over_time_networkx(node_type, attribute)

    elif query == "Plot attribute of a Node id over timestamps.":
        st.write("This query generates a plot of the value of a specific node attribute for a given node ID over timestamps, providing insights into the temporal trend of the attribute.")
        node_type = st.selectbox("Select Node Type:", options=node_data.keys())
        node_id = st.selectbox("Select Node Type:", options=all_id[node_type])
        attribute = st.selectbox("Select Attribute:", options=node_data[node_type])
        if st.button("Plot Trend"):
            plot_attribute_for_node_streamlit(node_id, attribute)

    elif query == "Plot average of an edge attribute over timestamps.":
        st.write("This query generates a plot of the average value of an edge attribute for a given edge type over timestamps, providing insights into the temporal trend of the attribute.")
        edge_type = st.selectbox("Select Edge Type:", options=edge_data.keys())
        attribute = st.selectbox("Select Edge Attribute:", options=edge_data[edge_type])
        if st.button("Plot Trend"):
            track_edge_attribute_over_time_streamlit(edge_type, attribute)

    elif query == "Anomaly Detection in Attributes.":
        st.write("This query detects timestamp where an attribute significantly deviates from its historical average, indicating potential anomalies.")
        node_type = st.selectbox("Select Node Type:", options=node_data.keys())
        attribute = st.selectbox("Select Node Attribute:", options=node_data[node_type])
        z_threshold = st.number_input(
        "Enter Z-Score Threshold",
        min_value=0.1,
        max_value=5.0,
        value=1.1,
        step=0.1,
        help="Anomaly is detected when the z-score is above or below this threshold."
        )
        st.code("Threshold=μ+z⋅σ")
        st.image(
        "https://miro.medium.com/v2/resize:fit:1400/1*Mk6EV8oIB1jlbQWcRzNRdg.png", 
        caption="Image from the Web", 
        use_column_width=True
        )
        if st.button("Detect Fluctuations"):
            detect_anomalies("BusinessGroup", "revenue",z_threshold)
if __name__ == "__main__":
    main()