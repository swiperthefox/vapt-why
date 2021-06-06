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

def what_apt_want(pkgs):
    return [parse_pkg_spec(line)[0] for line in install_command_output(pkgs)]
    
DEP_LEVEL = {
    'Depends': 2, 'PreDepends': 2, 'Recommends': 1, 'Suggests': 0
}

SUG = 0
REC = 1
DEP = 2
PKG_SHAPE = {SUG: 'octagon', REC: 'box', DEP: 'oval'}

edge_style = {
    #'Depends': 
    DEP: {'style': 'solid'}, 'PreDepends': {'style':'solid'}, 
    #'Recommends': 
    REC: {'style':'dashed', 'color': 'gray'},
    #'Suggests':
    SUG: {'style':'dotted', 'color': 'gray'}
}

def build_dep_map(pkgs):
    repo = apt.Cache()
    dep_map = {}
    pkg_set = set(pkgs)
    for pname in reversed(pkgs):
        pkg = repo[pname].candidate
        for dep_type, dep_level in DEP_LEVEL.items():
            depends = pkg.get_dependencies(dep_type)
            for entry in depends:
                for alternative in entry:
                    if alternative.name in pkg_set:
                        dep_map.setdefault(pname, {})[alternative.name] = dep_level
    return dep_map
    
def build_pkg_level_map(dep_map, starts):
    """For the packages in dep_map, determine their "dependency type".
    
    Debian pacakges have a few kinds of dependency: Depends, Recommends, and Suggests,
    which defines different "importance" levels of the dependencies for their parent pacakge.
    
    The "importance level" of a package can be DEP, REC, or SUG, DEP > REC > SUG.
    Rules to decide the level of a package:
    1. Packages in starts has type DEP.
    2. If a package has type DEP, then all its depends has type DEP.
    3. The recommends of a pacakge has importance level REC.
    4. The suggests of a pacakge has importance level SUG.
    5. If a package is required by multiple packages, its level is maximum of the levels it get from
    its parent packages. For example, if both A, B has level DEP, A depends on C, and B recommends C,
    then C get level DEP from A and level REC from B, so C's level is DEP. 
    """
    # This is basically a BFS.
    
    pkg_level_map = {pkg: DEP for pkg in starts}
    change_set = set(starts)
    while change_set:
        new_change_set = set()
        for pkg in change_set:
            pkg_type = pkg_level_map[pkg]
            for dep_pkg, dep_level in dep_map.get(pkg, {}).items():
                dep_level_from_path = min(pkg_type, dep_level)
                if dep_pkg not in pkg_level_map: # never got a level before
                    new_change_set.add(dep_pkg)
                    pkg_level_map[dep_pkg] = dep_level_from_path
                else:
                    if dep_level_from_path > pkg_level_map[dep_pkg]: # got a higher level
                        new_change_set.add(dep_pkg)
                        pkg_level_map[dep_pkg] = dep_level_from_path
        change_set = new_change_set
    return pkg_level_map


def render_depend_graph(depend_map, pkg_level_map, comment):
    graph = Digraph(comment = comment)
    graph.attr(rankdir="LR")
    nodes = set()

    def get_node(name):
        "create a node for `name` if needed."
        if name not in nodes:
            graph.node(name, shape = PKG_SHAPE[pkg_level_map[name]])
            nodes.add(name)
        return name

    for p, deps in depend_map.items():
        for dp, dep_level in deps.items():
            p = get_node(p)
            dp = get_node(dp)
            graph.edge(p, dp, **edge_style[dep_level])
    return graph
    
def legend_graph():
    "Generate a subgraph that shows the legends."
    node_idx = 0
    def make_edge(label, n2_style):
        nonlocal node_idx
        n1, n2 = str(node_idx), str(node_idx+1)
        legends.node(n1, label="package_1")
        legends.node(n2, label="package_2", **n2_style)
        legends.edge(n1, n2, label=label, **edge_style[DEP_LEVEL[label]])
        node_idx += 2
        return n1, n2
    legends = Digraph(name="cluster_0", comment="legends")
    legends.attr(label="Legends", shape="rectangle")
    legends.attr(rankdir="LR")
    legends.node('sp', "Suggested Package", shape=PKG_SHAPE[SUG])
    legends.node("dp", "Required Pakage", shape=PKG_SHAPE[DEP])
    legends.node("rp", "Optional Package", shape=PKG_SHAPE[REC])
    legends.edge("sp", "rp", style="invis")
    legends.edge("rp", "dp", style="invis")
    d1, d2 = make_edge("Depends", {'shape':PKG_SHAPE[DEP]})
    r1, r2 = make_edge("Recommends", {'shape':PKG_SHAPE[REC]})
    s1, s2 = make_edge("Suggests", {'shape':PKG_SHAPE[SUG]})
    legends.body.append(f"{{rank=min;sp;{d1};{r1};{s1}}}")
    legends.body.append(f'{{rank=max;dp;{d2};{r2};{s2}}}')
    return legends
    
if __name__ == '__main__':
    import sys
    starts = sys.argv[1:]
    pkgs = what_apt_want(starts)
    dep_map = build_dep_map(pkgs)
    pkg_type_map = build_pkg_level_map(dep_map, starts)
    graph = render_depend_graph(dep_map, pkg_type_map, "Dependency graph")
    graph.subgraph(legend_graph())
    graph.view()