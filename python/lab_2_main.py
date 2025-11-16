from graphviz import Digraph

g = Digraph("NestedClusters", format="svg")
g.attr(rankdir="LR", fontsize="10", fontname="Helvetica")
g.attr("node", shape="box", style="rounded,filled", fillcolor="lightgray")

with g.subgraph(name="cluster_outer") as outer:
    outer.attr(label="Outer", color="lightblue")

    # Подкластер 1
    with outer.subgraph(name="cluster_inner_1") as c1:
        c1.attr(label="Inner 1", color="lightgreen")
        c1.node("A1", "A1")
        c1.node("A2", "A2")
        c1.edge("A1", "A2")

    # Подкластер 2
    with outer.subgraph(name="cluster_inner_2") as c2:
        c2.attr(label="Inner 2", color="lightpink")
        c2.node("B1", "B1")
        c2.node("B2", "B2")
        c2.edge("B1", "B2")

# Между подкластерными узлами — обычные связи
g.edge("A2", "B1")

g.render("nested_clusters_example", view=True)
