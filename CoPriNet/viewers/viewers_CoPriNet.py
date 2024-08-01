import os
import json
import webbrowser
from jinja2 import Template
import pyworkflow.viewer as pwviewer
from pyworkflow.protocol import params
from CoPriNet.protocols.protocol_CoPriNet import ProtChemCoPriNet



class ProtChemCoPriNetViewer(pwviewer.ProtocolViewer):
    """ Viewer for ProtChemAiZynthFinder protocol """
    _label = 'View JSON and Reactions'
    _targets = [ProtChemCoPriNet]

    def __init__(self, **args):
        super().__init__(**args)


