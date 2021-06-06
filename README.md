## Usage

Download the source, install the python pacakges `graphviz` and `python-apt`. Then run
    
    python src/main.py package_1 pacakge_2
    
It will show a graphic dependency tree of the pacakges that needs to be installed.


## Why It is Useful

Sometimes when installing a package (target package) in Debian Linux, the
package manager might want to pull in some seemingly unrelated packages
(suprising depends). This tool helps the user to understand why such a package
is included.

By looking at the dependency tree, we can see the dependency chain from the `target
package` to the `suprising depends` and other information like wether it is a
strict dependant, or it's just optional one?

## Difference From Similar tools

* The `why` command of `apt-get`

  The `why` command shows why a pacakge would be installed, but there are two
  differences:

  1. It shows why a package would be installed as dependencies of any **already
      installed** pacakge.

  2. It only shows **one** dependency chain between the packages that installed
      pacakge and the given one.

* debtree

  Debtree generates a dot file that includes **all** dependencies of a given
  package, regardless wether they are installed or not. This results in a very
  complex graph, and it's hard to see which *new* packages will be installed and
  why.