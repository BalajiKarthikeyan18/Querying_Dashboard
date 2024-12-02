import streamlit as st
import json
import functools
import time
import tracemalloc
import plotly.graph_objects as go
import base64

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

    st.title("Querying across Timestamps")

    queries = ["Select",
            "Plot average of a node attribute over timestamps.",
            "Plot attribute of a Node id over timestamps.",
            "Plot average of an edge attribute over timestamps."
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

if __name__ == "__main__":
    main()