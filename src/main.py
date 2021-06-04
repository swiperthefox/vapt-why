import apt
import subprocess
from graphviz import Digraph

def install_command_output(pkgs):
    install = subprocess.Popen(('apt-get', 'install', '--dry-run', *pkgs), stdout=subprocess.PIPE)
    output = subprocess.check_output(('grep', '^Inst'), stdin=install.stdout)
    return output.decode('ascii').splitlines()

def parse_pkg_spec(line):
    # Inst libffi-dev (3.3-6 Debian:testing [amd64])
    #pattern = '^Inst (?P<pkg>\S+)\s+\(?P<version>\S+)\s+(?P<distribution>\S+)\s\[(?P<arch>\S+)\]\)$'
    items = line.split()
    if len(items) != 5:
        print("bad format:", line)
        return None
    (_, pkg_name, version, distribution, arch) = items
    return (pkg_name, version[1:], distribution, arch[1:-1])
    
DEP_VALUE = {
    'Depends': 2, 'PreDepends': 2, 'Recommends': 1, 'Suggests': 0
}

SUG = 0
REC = 1
DEP = 2

def build_dep_map(pkgs):
    repo = apt.Cache()
    dep_map = {}
    pkg_set = set(pkgs)
    for pname in reversed(pkgs):
        pkg = repo[pname].candidate
        for dep_type in ['Depends', 'PreDepends', 'Recommends', 'Suggests']:
            depends = pkg.get_dependencies(dep_type)
            for entry in depends:
                for alternative in entry:
                    if alternative.name in pkg_set:
                        dep_map.setdefault(pname, {})[alternative.name] = dep_type
    return dep_map
    
def build_pkg_type_map(dep_map, starts):
    """For the packages in dep_map, determine their "dependency type".
    
    The "dependency type" of package can be "depends", "recommends", or "suggests".
    """
    pkg_type_map = {pkg: DEP for pkg in starts}
    change_set = set(starts)
    while change_set:
        new_change_set = set()
        for pkg in change_set:
            pkg_type = pkg_type_map[pkg]
            for dep_pkg, dep_type in dep_map.get(pkg, {}).items():
                dep_value = DEP_VALUE[dep_type]
                type_from_path = min(pkg_type, dep_value)
                if dep_pkg not in pkg_type_map:
                    new_change_set.add(dep_pkg)
                    pkg_type_map[dep_pkg] = type_from_path
                else:
                    if type_from_path > pkg_type_map[dep_pkg]:
                        new_change_set.add(dep_pkg)
                        pkg_type_map[dep_pkg] = type_from_path
        change_set = new_change_set
    return pkg_type_map

edge_style = {
    'Depends': 'solid', 'PreDepends': 'solid', 'Recommends': 'dashed', 'Suggests': 'tapered'
}

def render_depend_graph(depend_map, pkg_type_map, comment):
    graph = Digraph(comment = comment)
    graph.attr(rankdir="LR")
    nodes = set()
    SHAPE = {0: 'polygon', 1: 'box', 2: 'oval'}
    def get_node(name):
        if name not in nodes:
            graph.node(name, shape = SHAPE[pkg_type_map[name]])
            nodes.add(name)
        return name

    for p, deps in depend_map.items():
        for dp, dep_type in deps.items():
            p = get_node(p)
            dp = get_node(dp)
            # graph.attr(style=edge_style[dep_type])
            graph.edge(p, dp, style=edge_style[dep_type])
    return graph
    
def legend_graph():
    node_idx = 0
    def make_edge(label, n2_style, edge_style):
        nonlocal node_idx
        n1, n2 = str(node_idx), str(node_idx+1)
        legends.node(n1, label="package_1")
        legends.node(n2, label="package_2", **n2_style)
        legends.edge(n1, n2, label=label, **edge_style)
        node_idx += 2
    legends = Digraph(name="cluster_0", comment="legends")
    legends.attr(label="Legends", shape="rectangle")
    legends.attr(rankdir="LR")
    legends.node("dp", "Required Pakage", shape='oval')
    legends.node("op", "Optional Package", shape="box")
    legends.edge("dp", "op", style="invis")
    make_edge("Depends", {'shape':"oval"}, {'style':'solid'})
    make_edge("Recommends", {'shape':"box"}, {'style':edge_style['Recommends']})
    make_edge("Suggests", {'shape':"box"}, {'style':edge_style['Suggests']})
    return legends
    
if __name__ == '__main__':
    import sys
    starts = sys.argv[1:]
    output = install_command_output(starts)
    pkgs = [parse_pkg_spec(line)[0] for line in output]
    dep_map = build_dep_map(pkgs)
    pkg_type_map = build_pkg_type_map(dep_map, starts)
    graph = render_depend_graph(dep_map, pkg_type_map, "Dependency graph")
    graph.subgraph(legend_graph())
    # graph = graph.unflatten(stagger=10)
    graph.view()