Show graphic dependency tree between Debian packages.

## The problem

While installing a package in Debian Linux, the package manager might want to pull in some seemingly unrelated packages. The output of apt tools only shows a list of packages to be installed but doesn't show why these packages are included.

## The solution

This program will show a graphic dependency tree between the packages to be installed, so you can know why a package is included? Is it a strict dependant, or it's just optional?

## Usage

Download the source, install the python `graphviz` and `python-apt` packages. Then run
    
    python src/main.py package_name
    
Note: if you can't install the `python-apt` package via `pip`, there is a system package that can be installed using apt.

