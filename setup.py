#!/usr/bin/python
from setuptools import setup, find_packages
from glob import glob

setup(
	name = "nisotools",
	version = "0.1svn",
	packages = find_packages(),
	zip_safe = False,
	
	data_files = [
		("share/nisotools/glade", glob("*/*.glade"))
	],
	
	entry_points = {
		'console_scripts': [
			"nisomounter = nisomounter.nisomounter:main"
		]
	}
)
