# **************************************************************************
# *
# * Authors: Verónica Gamo (veronica.gamoparejo@usp.ceu.es)
# *
# * Biocomputing Unit, CNB-CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

# Scipion em imports
import os, subprocess
from subprocess import run
from scipion.install.funcs import InstallHelper

# Scipion chem imports
import pwchem

# Plugin imports
from .constants import PLUGIN_VERSION, COPRINET_DIC

_version_ = PLUGIN_VERSION
_logo = ""
_references = ['']

class Plugin(pwchem.Plugin):
	@classmethod
	def _defineVariables(cls):
		""" Return and write a variable in the config file. """
		cls._defineEmVar(COPRINET_DIC['home'], '{}-{}'.format(COPRINET_DIC['name'], COPRINET_DIC['version']))

	@classmethod
	def defineBinaries(cls, env):
		""" Install the necessary packages. """
		cls.addCoPriNet(env)

	########################### PACKAGE FUNCTIONS ###########################

	@classmethod
	def addCoPriNet(cls, env, default=True):
		""" This function installs CoPriNet's package. """
		# Instantiating install helper
		installer = InstallHelper(COPRINET_DIC['name'], packageHome=cls.getVar(COPRINET_DIC['home']), packageVersion=COPRINET_DIC['version'])
		installer.addCommand('git clone https://github.com/oxpig/CoPriNet.git') \
		.addCommand(f'cd CoPriNet && conda env create -f CoPriNet_env.yml ') \
		.addPackage(env, dependencies=['conda'], default=default)

	@classmethod
	def runCoPriNet(cls, program, args, cwd=None):
			""" Run CoPriNet command from a given protocol. """
			activation_command = '{}conda activate {}'.format(cls.getCondaActivationCmd(), "CoPriNet")
			dir=os.path.join(cls.getVar(COPRINET_DIC['home']), "CoPriNet")
			full_program = f'{activation_command} && cd {dir} && {program} {args}'
			run(full_program, env=cls.getEnviron(), cwd=cwd, shell= True)
	






	
