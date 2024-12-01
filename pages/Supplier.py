import streamlit as st
import time  # Ensure this is imported properly
import tracemalloc
import functools
import json


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
def supplier_reliability_costing_temporal(graph, reliability_threshold, max_transportation_cost):
    """
    Analyze supplier reliability and transportation costs at a specific timestamp in a temporal graph.

    Parameters:
        tg (TemporalGraph): The temporal graph object.
        timestamp (int): The specific timestamp to analyze.
        reliability_threshold (float): The maximum acceptable reliability threshold for suppliers.
        max_transportation_cost (float): The maximum acceptable transportation cost.

    Returns:
        list: A list of suppliers meeting the criteria, including supplier ID, reliability, and transportation cost.
    """
    # Load the graph for the specified timestamp

    suppliers = []

    # Iterate through edges to find SupplierToWarehouse relationships
    for u, v, data in graph.edges(data=True):

        if data.get("relationship_type") == "SupplierToWarehouse":

            transportation_cost = data.get("transportation_cost", 0)

            # Check transportation cost and reliability
            if transportation_cost >= max_transportation_cost:
                reliability = graph.nodes[u].get("reliability", 0)
                if reliability <= reliability_threshold:
                    suppliers.append((u, reliability, transportation_cost))

    return suppliers


@time_and_memory
def supplier_reliability_costing_json(json_graph, reliability_threshold, max_transportation_cost):
    """
    Analyze supplier reliability and transportation costs at a specific timestamp in a temporal graph.

    Parameters:
        tg (TemporalGraph): The temporal graph object.
        timestamp (int): The specific timestamp to analyze.
        reliability_threshold (float): The maximum acceptable reliability threshold for suppliers.
        max_transportation_cost (float): The maximum acceptable transportation cost.

    Returns:
        list: A list of suppliers meeting the criteria, including supplier ID, reliability, and transportation cost.
    """
    # Load the graph for the specified timestamp
    suppliers = []

    # Iterate through edges to find SupplierToWarehouse relationships
    for i in json_graph["relationship_values"]:

        if i[0] == "SupplierToWarehouse":

            transportation_cost = i[1]

            # Check transportation cost and reliability
            if transportation_cost >= max_transportation_cost:
                supplier_id = i[-2]
                # reliability =
                for nodes in json_graph["node_values"]["Supplier"]:
                    if nodes[-1] == supplier_id:
                        reliability = nodes[3]
                        break

                if reliability <= reliability_threshold:
                    suppliers.append(
                        (supplier_id, reliability, transportation_cost))

    return suppliers


@time_and_memory
def query_supplied_part_types_for_supplier(G, supplier_id):
    if supplier_id in G.nodes and G.nodes[supplier_id].get("node_type") == "Supplier":
        supplied_part_types = G.nodes[supplier_id].get("supplied_part_types")
        return supplied_part_types
    else:
        return None


@time_and_memory
def query_supplied_part_types_for_supplier_json(json_graph, supplier_id):
    for nodes in json_graph["node_values"]["Supplier"]:
        if nodes[-1] == supplier_id:
            return nodes[-2]
    return None


def main():

    if "temporal_graph" not in st.session_state:
        st.error(
            "No Temporal Graph found in the session state. Please run the main script first.")
        return

    timestamp = st.select_slider("Select Timestamp", options=range(
        len(st.session_state.temporal_graph.files)))

    graph = st.session_state.temporal_graph.load_graph_at_timestamp(timestamp)

    with open(st.session_state.temporal_graph.files[timestamp], 'r') as f:
        json_graph = json.load(f)

    queries = st.selectbox("Select Query", [
                           "Select Query", "Supplier Reliability and Costing", "Supplied Part Types"])

    if queries == "Supplier Reliability and Costing":

        st.write(
            "This query will return suppliers meeting the criteria of reliability and transportation cost.")
        reliability_threshold = st.number_input(
            "Reliability Threshold", value=0.8, min_value=0.0, max_value=1.0, step=0.01)
        max_transportation_cost = st.number_input(
            "Max Transportation Cost", value=800, min_value=10, max_value=10000, step=10)

        # cols = st.columns(2)

        # with cols[0]:
        #     st.write("Result using Networkx:")
        #     suppliers = supplier_reliability_costing_temporal(graph, reliability_threshold, max_transportation_cost)
        #     if suppliers:
        #         for supplier in suppliers:
        #             st.write(f"Supplier ID: {supplier[0]}, Reliability: {supplier[1]}, Transportation Cost: {supplier[2]}")
        #     else:
        #         st.write("No suppliers meet the criteria.")

        # with cols[1]:
        #     st.write("Result using JSON:")
        #     suppliers = supplier_reliability_costing_json(json_graph, reliability_threshold, max_transportation_cost)

        #     if suppliers:
        #         for supplier in suppliers:
        #             st.write(f"Supplier ID: {supplier[0]}, Reliability: {supplier[1]}, Transportation Cost: {supplier[2]}")
        #     else:
        #         st.write("No suppliers meet the criteria.")

        # Two-column layout for displaying results
        cols = st.columns(2, gap="large")

        # Define styles for success and error messages
        success_style = "color: white; font-weight: bold;"
        error_style = "color: red; font-weight: bold;"

        # Left column: Results using Networkx
        with cols[0]:
            st.markdown("### 🌐 Result using **Networkx**")
            st.divider()  # Optional: Add a horizontal line for separation

            suppliers_networkx = supplier_reliability_costing_temporal(
                graph, reliability_threshold, max_transportation_cost)

            if suppliers_networkx:
                for supplier in suppliers_networkx:
                    st.markdown(
                        f"""
                        <div style="{success_style}">
                        Supplier ID: `{supplier[0]}`<br>
                        Reliability: `{supplier[1]:.4f}`<br>
                        Transportation Cost: `{supplier[2]:.2f}`
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.divider()
            else:
                st.markdown(
                    f"<div style='{error_style}'>No suppliers meet the criteria.</div>",
                    unsafe_allow_html=True,
                )

        # Right column: Results using JSON
        with cols[1]:
            st.markdown("### 🗃️ Result using **JSON**")
            st.divider()  # Optional: Add a horizontal line for separation

            suppliers_json = supplier_reliability_costing_json(
                json_graph, reliability_threshold, max_transportation_cost)

            if suppliers_json:
                for supplier in suppliers_json:
                    st.markdown(
                        f"""
                        <div style="{success_style}">
                        Supplier ID: `{supplier[0]}`<br>
                        Reliability: `{supplier[1]:.4f}`<br>
                        Transportation Cost: `{supplier[2]:.2f}`
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.divider()
            else:
                st.markdown(
                    f"<div style='{error_style}'>No suppliers meet the criteria.</div>",
                    unsafe_allow_html=True,
                )

        # Add spacing for better layout management
        # st.write("---")

    elif queries == "Supplied Part Types":
        st.write(
            "This query will return the part types supplied by a specific supplier.")

        # supplier_id = st.number_input("Supplier ID", value=0)
        all_suppliers = [node for node in graph.nodes if graph.nodes[node].get(
            "node_type") == "Supplier"]
        supplier_id = st.selectbox("Select Supplier ID", options=all_suppliers)

        cols = st.columns(2, gap="large")

        # Define styles for success and error messages
        success_style = "color: white; font-weight: bold;"
        error_style = "color: red; font-weight: bold;"

        with cols[0]:
            st.markdown("### 🌐 Result using **Networkx**")
            supplied_part_types = query_supplied_part_types_for_supplier(
                graph, supplier_id)

            if supplied_part_types is not None:
                st.markdown(
                    f" #### Supplier {supplier_id} supplies the following part types:",
                    unsafe_allow_html=True,
                )

                for part_type in supplied_part_types:
                    st.markdown(
                        f"<div style='{success_style}'>{part_type}</div>",
                        unsafe_allow_html=True,
                    )

            else:
                st.markdown(
                    f"<div style='{error_style}'>Supplier {supplier_id} does not exist in the graph or is not a supplier.</div>",
                    unsafe_allow_html=True,
                )

        with cols[1]:
            st.write("### 🗃️ Result using **JSON**")
            supplied_part_types = query_supplied_part_types_for_supplier_json(
                json_graph, supplier_id)

            if supplied_part_types is not None:
                st.markdown(
                    f" #### Supplier {supplier_id} supplies the following part types:",
                    unsafe_allow_html=True,
                )

                for part_type in supplied_part_types:
                    st.markdown(
                        f"<div style='{success_style}'>{part_type}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    f"<div style='{error_style}'>Supplier {supplier_id} does not exist in the graph or is not a supplier.</div>",
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
