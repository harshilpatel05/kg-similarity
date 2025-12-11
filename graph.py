import networkx
import csv
import matplotlib.pyplot as plot
import streamlit
from collections import deque

def createGraph(filePath):
    graph = networkx.Graph()
    with open(filePath, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            product_id = row["id"]
            category = row["category"]
            brand = row["brand"]
            price = float(row["price"])
            stock = row["stock"].lower() == "true"
            tags = row["tags"].split(";")

            # Create the product as a graph node
            graph.add_node(
                product_id,
                type="product",
                brand=brand,
                category=category,
                price=price,
                stock=stock,
                tags=tags
            )

            # Category nodes point to product
            if category not in graph.nodes:
                graph.add_node(category, type="category")

            graph.add_edge(product_id, category, relation="IS A")

            # Tag nodes
            for tag in tags:
                if tag not in graph.nodes:
                    graph.add_node(tag, type="tag")
                graph.add_edge(product_id, tag, relation="HAS TAG")

    return graph



def visualizeGraph(graph):
    plot.figure(figsize=(14, 10))
    pos = networkx.spring_layout(graph, seed=42)

    productNodes = [nodes for nodes, dict in graph.nodes(data=True) if dict["type"] == "product"]
    categoryNodes = [nodes for nodes, dict in graph.nodes(data=True) if dict["type"] == "category"]
    tagNodes = [n for n, d in graph.nodes(data=True) if d["type"] == "tag"]

    networkx.draw_networkx_nodes(graph, pos, nodelist=productNodes, node_color="skyblue", node_size=600, label="Products")
    networkx.draw_networkx_nodes(graph, pos, nodelist=categoryNodes, node_color="lightgreen", node_size=700, label="Categories")
    networkx.draw_networkx_nodes(graph, pos, nodelist=tagNodes, node_color="orange", node_size=500, label="Tags")

    networkx.draw_networkx_edges(graph, pos, width=1.5)
    networkx.draw_networkx_labels(graph, pos, font_size=8, font_weight="bold")

    edgeLabels = networkx.get_edge_attributes(graph, "relation")
    networkx.draw_networkx_edge_labels(graph, pos, edge_labels=edgeLabels, font_size=7)

    plot.title("Knowledge Graph Visualization", fontsize=16)
    plot.legend(scatterpoints=1)
    plot.axis("off")
    plot.show()


def bfsSearch(graph, startProduct):
    visited = set()
    queue = deque([startProduct])
    productList = []

    while queue:
        node = queue.popleft()

        if node in visited:
            continue

        visited.add(node)

        # Filter out tags and category nodes
        nodeData = graph.nodes[node]
        if node != startProduct and nodeData.get("type") == "product":
            productList.append(node)

        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                queue.append(neighbor)

    return productList



def checkConstraints(graph, productId, maxPrice, requiredTags, preferredBrand):
    data = graph.nodes[productId]

    # If product is not in stock then we skip it
    if (data["stock"] == 0):
        return False
    # If product price is more than the max price then we skip it
    if (data["price"] > maxPrice):
        return False
    # Match the product tags with the required tags
    for tag in requiredTags:
        if tag not in data["tags"]:
            return False
    # If there is a brand preference check if product is of that brand if not then skip
    if preferredBrand is not None and preferredBrand != "" and data["brand"] != preferredBrand:
        return False

    return True


def scoreCandidate(graph, requestedProduct, candidateProduct):
    requestedData = graph.nodes[requestedProduct]
    candidateData = graph.nodes[candidateProduct]

    score = 0

    requestedCategory = requestedData["category"]
    candidateCategory = candidateData["category"]

    if requestedCategory == candidateCategory:
        score += 3
    else:
        # similar category if category nodes are directly connected in graph
        for neighbor in graph.neighbors(requestedCategory):
            if neighbor == candidateCategory:
                score += 1
                break

    # Brand match
    if requestedData["brand"] == candidateData["brand"]:
        score += 1

    # Cheaper option 
    if candidateData["price"] < requestedData["price"]:
        score += 1

    return score


def explainRules(graph, requestedProduct, candidateProduct, requiredTags):
    requestedData = graph.nodes[requestedProduct]
    candidateData = graph.nodes[candidateProduct]

    rules = []

    if requestedData["category"] == candidateData["category"]:
        rules.append("Same Category")
    else:
        rules.append("Similar Category")

    if all(tag in candidateData["tags"] for tag in requiredTags):
        rules.append("All tags matched")

    if candidateData["price"] < requestedData["price"]:
        rules.append("Cheaper than original")

    if candidateData["brand"] == requestedData["brand"]:
        rules.append("Same brand")
    else:
        rules.append("Different brand")

    return rules


def findAlternatives(graph, requestedProduct, maxPrice, requiredTags, preferredBrand):
    if requestedProduct not in graph.nodes:
        return []

    reqData = graph.nodes[requestedProduct]

    # if product itself is in stock then we dont need to find similar
    if reqData["stock"]:
        return [("EXACT_MATCH", requestedProduct, 999, ["product_in_stock"])]

    candidateProducts = bfsSearch(graph, requestedProduct)

    validList = []
    for productId in candidateProducts:
        if checkConstraints(graph, productId, maxPrice, requiredTags, preferredBrand):
            score = scoreCandidate(graph, requestedProduct, productId)
            rules = explainRules(graph, requestedProduct, productId, requiredTags)
            validList.append((productId, score, rules))

    # sort by score
    validList.sort(key=lambda x: x[1], reverse=True)

    return validList[:3]




def runStreamlitApp():
    streamlit.title("Knowledge Graph Based Similar Product Search")

    filePath = "products.csv"
    graph = createGraph(filePath)

    # Get list of products
    productOptions = sorted(
        [n for n, d in graph.nodes(data=True) if d.get("type") == "product"]
    )

    streamlit.sidebar.header("Input Parameters")

    requestedProduct = streamlit.sidebar.selectbox("Requested product", productOptions)

    maxPrice = streamlit.sidebar.number_input(
        "Maximum price",
        min_value=0.0,
        value=float(graph.nodes[requestedProduct]["price"]),
        step=1.0
    )

    requiredTagsText = streamlit.sidebar.text_input(
        "Required tags (separated by ';')",
        value=""
    )
    requiredTags = [t.strip() for t in requiredTagsText.split(";") if t.strip()]

    preferredBrandInput = streamlit.sidebar.text_input(
        "Preferred brand (optional)",
        value=""
    )
    preferredBrand = preferredBrandInput.strip() if preferredBrandInput.strip() != "" else None

    if streamlit.sidebar.button("Find Alternatives"):
        streamlit.subheader("Results")

        # Check if requested product is in stock
        reqData = graph.nodes[requestedProduct]
        if reqData["stock"]:
            streamlit.success("Exact product is in stock.")
            streamlit.write("**Product ID:**", requestedProduct)
            streamlit.write("**Brand:**", reqData["brand"])
            streamlit.write("**Category:**", reqData["category"])
            streamlit.write("**Price:**", reqData["price"])
            streamlit.write("**Tags:**", ", ".join(reqData["tags"]))
        else:
            results = findAlternatives(graph, requestedProduct, maxPrice, requiredTags, preferredBrand)

            if not results:
                streamlit.error("No suitable alternatives found with the given constraints.")
            else:
                for idx, item in enumerate(results, start=1):
                    productId, score, rules = item
                    data = graph.nodes[productId]
                    streamlit.markdown(f"### Alternative {idx}")
                    streamlit.write("**Product ID:**", productId)
                    streamlit.write("**Brand:**", data["brand"])
                    streamlit.write("**Category:**", data["category"])
                    streamlit.write("**Price:**", data["price"])
                    streamlit.write("**Tags:**", ", ".join(data["tags"]))
                    streamlit.write("**Score:**", score)
                    streamlit.write("**Rule tags:**", ", ".join(rules))
                    streamlit.markdown("---")

    streamlit.markdown("----")





if __name__ == "__main__":
    runStreamlitApp()
