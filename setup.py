# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from codecs import open
from os import path

# Import plugin's version
from CoPriNet.constants import PLUGIN_VERSION

# Get current path
here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
	long_description = f.read()

# Get requirements
with open('requirements.txt') as f:
	requirements = f.read().splitlines()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.
setup(
	name='scipion-chem-coprinet',  # Required
	version=PLUGIN_VERSION,  # Required
	description='Scipion framework plugin for the use of CoPriNet software tools',  # Required
	long_description=long_description,  # Optional
	url='https://github.com/scipion-chem/scipion-chem-coprinet',  # Optional
	author='Verónica Gamo',  # Optional
	author_email='veronica.gamoparejo@usp.ceu.es',  # Optional
	keywords='scipion CoPriNet scipion-3.0 cheminformatics',  # Optional
	packages=find_packages(),
	install_requires=[requirements],
	entry_points={'pyworkflow.plugin': 'CoPriNet = CoPriNet'}#,
	#package_data={  # Optional
	#   'CoPriNet': ['coprinet_logo.png', 'protocols.conf'],
	#}
)
