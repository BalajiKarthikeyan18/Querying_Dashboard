def query_parts_for_product_offering(graph, product_offering_id):
    """
    Retrieve all parts needed to manufacture a given product offering based on the schema.
    """
    parts = set()
    
    # Traverse Facility -> ProductOffering relationships
    for facility, facility_data in graph.nodes(data=True):
        if facility_data.get("node_type") == "Facility":
            if graph.has_edge(facility, product_offering_id):
                edge_data = graph[facility][product_offering_id]
                if edge_data.get("relationship_type") == "FacilityToProductOfferings":
                    
                    # Traverse Parts -> Facility relationships
                    for part, part_data in graph.nodes(data=True):
                        if part_data.get("node_type") == "Parts" and graph.has_edge(part, facility):
                            part_edge_data = graph[part][facility]
                            if part_edge_data.get("relationship_type") == "PartsToFacility":
                                parts.add(part)
    
    return list(parts)



def query_profitable_products(graph, cost_threshold, demand_threshold):
    """
    Retrieve profitable products based on cost and demand thresholds.
    """
    profitable_products = []
    for node, attrs in graph.nodes(data=True):
        if attrs.get("node_type") == "ProductOffering":
            making_cost = attrs.get("cost", float("inf"))
            demand = attrs.get("demand", 0)

            if making_cost <= cost_threshold and demand >= demand_threshold:
                profitable_products.append((node, making_cost, demand))

    return profitable_products
