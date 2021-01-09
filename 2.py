# 2021 - github.com/ufukty
# GPL-3.0 License
# See the LICENSE file

import json
import os

from datetime import datetime
from pickletools import pickle

import networkx as nx
from matplotlib import pyplot as plt
from matplotlib import collections

# ------------------------------------------------------------- #
# Configuration
# ------------------------------------------------------------- #

# Subreddit locations will be read from graph_layout.pickle file
# if its True, if its not then 1 random layout will be create and
# will be written to graph_layout.pickle file
read_graph_layout_file = False

# Script can render each layer at different runs
draw_edge_sources = False
draw_edge_targets = False
draw_subreddit_names = True

# ------------------------------------------------------------- #
# Functions
# ------------------------------------------------------------- #

dir_path = os.path.abspath(__file__ + "/..")


def is_a_json_file(path: str):
    filename_parts = path.rsplit(".", 1)
    return (len(filename_parts) > 1 and filename_parts[1] == "json")


def filenames_of_json_files_in(folder: str):
    return sorted([path for path in os.listdir(dir_path + "/" + folder) if is_a_json_file(path)])


def load_data(folder: str):
    print("reading folder:", folder)
    
    return_list = []
    for file_path in filenames_of_json_files_in(folder=folder):
        with open(dir_path + "/" + folder + "/" + file_path, "r") as f:
            for line in f.readlines():
                return_list.append(json.loads(line))
    return return_list


def populate_graph(G: nx.Graph, degrees: list):
    print("populating the graph")
    weight_list = []
    
    for degree_dict in degrees:
        G.add_node(degree_dict["subreddit"])
    
    for link in load_data("spark_output/links"):
        G.add_edge(link["source"], link["target"])
        weight_list.append(link["cnt"])
    
    return weight_list


source_color = [255, 139, 87] # orange
target_color = [87, 181, 255] # blue


def line_split(
    start: tuple,
    end: tuple,
    weight: float,
    pieces: int,
    draw_sources: bool = False,
    draw_targets: bool = False
):
    
    ax = plt.gca()
    
    end_y, end_x = end
    start_y, start_x = start
    
    step_y, step_x = (end_y - start_y) / pieces, (end_x - start_x) / pieces
    step_opacity = 255 / pieces
    
    segments, color, line_widths = [], [], []
    pieces_will_be_drawed = []
    if draw_sources:
        pieces_will_be_drawed += list(range(0, pieces // 2))
    if draw_targets:
        pieces_will_be_drawed += list(range(pieces // 2, pieces))
    
    for i in pieces_will_be_drawed:
        segments.append(
            [
                [start_y + step_y * i, start_x + step_x * i],
                [start_y + step_y * (i + 1), start_x + step_x * (i + 1)]
            ]
        )
        if draw_sources:
            rgb = source_color
        elif draw_targets:
            rgb = target_color
        else:
            raise Exception()
        rgba = rgb + [((i - (pieces / 2))**2 / (pieces / 2)**2) * 255 * weight]
        color += [[float(channel) / 255 for channel in rgba]]
        line_widths += [0.2]
    return segments, color, line_widths


def draw_labels(G: nx.Graph, pos: dict, subreddits: list):
    print("drawing labels")
    
    G = nx.Graph().add_nodes_from(subreddits)
    pos = {sub: point_yx for sub, point_yx in pos.items() if sub in subreddits}
    labels = {sub: sub for sub, point_yx in pos.items() if sub in subreddits}
    
    nx.draw_networkx_labels(
        G=G,
        pos=pos,
        labels=labels,
        font_color="#FFFFFF",
        font_size=1,
        font_family="monospace",
    )


def draw_edges(
    G: nx.Graph,
    pos: dict,
    weight_list: list,
    draw_sources: bool = False,
    draw_targets: bool = False
):
    print("drawing edges: 0.0%")
    
    max_weight = float(max(weight_list))
    edge_colors = [(0.34, 0.71, 1.0, float(w) / max_weight) for w in weight_list]
    
    total = len(list(G.edges()))
    ax = plt.gca()
    
    count = 0
    for i, edge in enumerate(list(G.edges())[:]):
        if i % 100 == 0:
            print("\r\033[1Adrawing edges: {}%  ".format(float(i) / total * 10000 // 1 / 100))
        from_node, to_node = edge
        segments, colors, line_widths = line_split(
            start=pos[from_node],
            end=pos[to_node],
            weight=0.02 + 0.98 * weight_list[i] / max_weight,
            pieces=20,
            draw_sources=draw_sources,
            draw_targets=draw_targets,
        )
        lc = collections.LineCollection(
            segments,
            colors=colors,
            linewidths=line_widths,
            antialiaseds=(1,),
            linestyle="solid",
            transOffset=ax.transData,
        )
        count += len(segments)
        lc.set_zorder(1)
        ax.add_collection(lc)
    print("segments added to ax:", count)


def save(fig: plt.Figure, ax: plt.Axes):
    print("saving")
    
    ax.set_xlim([-0.05, 1.05])
    ax.set_ylim([-0.05, 1.05])
    
    plt.subplots_adjust(
        left=0,
        right=1,
        bottom=0,
        top=1,
        wspace=0,
        hspace=0,
    )
    fig.text(0.98, 0.03, s="github.com/ufukty", color="#888888", size=4, ha="right")
    
    output_filename = datetime.now().strftime(dir_path + "/output %Y.%m.%d %H.%M.%S.png")
    plt.axis("off")
    plt.savefig(
        output_filename,
        dpi=1200,
        bbox_inches='tight',
        facecolor="#000000",
    )


def save_pos_data(pos: dict):
    pickle_file = open("graph_layout.picle", "ab")
    pickle.dump(pos, pickle_file)
    pickle_file.close()


def read_pos_data():
    pickle_file = open("graph_layout.picle", "rb")
    pos = pickle.load(pickle_file)
    pickle_file.close()
    return pos


if __name__ == "__main__":
    
    degrees = load_data("spark_output/degrees")
    
    G = nx.Graph()
    weight_list = populate_graph(G, degrees)
    
    if read_graph_layout_file:
        pos = read_pos_data()
    else:
        pos = nx.random_layout(G)
        save_pos_data(pos)
        pass
    
    fig, ax = plt.subplots(figsize=[6.4, 4.8])
    
    if draw_edge_sources:
        draw_edges(G, pos, weight_list, draw_sources=True)
    if draw_edge_targets:
        draw_edges(G, pos, weight_list, draw_targets=True)
    if draw_subreddit_names:
        top_sources = [d["subreddit"] for d in load_data("spark_output/top_sources")]
        top_targets = [d["subreddit"] for d in load_data("spark_output/top_targets")]
        top_subs = list(set(top_sources + top_targets))
        draw_labels(G, pos, top_subs)
    
    save(fig, ax)