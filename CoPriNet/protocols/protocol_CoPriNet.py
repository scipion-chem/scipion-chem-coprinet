################ VERÓNICA GAMO PAREJO ##############################

# General imports 
import os
import csv

# Specific imports
from pyworkflow.protocol.params import PointerParam, STEPS_PARALLEL
from pwem.protocols import EMProtocol
from pwchem.utils import *
from CoPriNet import Plugin
from pwchem.constants import RDKIT_DIC
import pyworkflow.object as pwobj
from pwchem.objects import SmallMolecule, SetOfSmallMolecules
from urllib.request import urlopen


RDKIT = 0

class ProtChemCoPriNet(EMProtocol):

    """ CoPriNet
    User IA Manual: CoPriNet Protocol

The CoPriNet protocol is designed to estimate the compound price of small
molecules using a graph neural network model trained on real-world pricing
data. It enables users to incorporate economic feasibility into compound
selection pipelines by predicting how expensive a molecule is likely to be,
based solely on its chemical structure.

To run the protocol, the user must provide a set of ligand structures in
standardized format, such as SDF or MOL files. Each compound is parsed and
converted into a molecular graph, which is then passed through the CoPriNet
model to compute a predicted price. The model does not require any
experimental or contextual metadata?only the 2D molecular topology is used.

The user can optionally specify whether the input compounds have been
preprocessed or whether additional cleaning or sanitization steps should be
performed. This can help resolve minor issues in atom types, aromaticity,
or hydrogen treatment before feeding the molecules to the neural network.

The protocol outputs a table where each compound is associated with a
predicted price value, typically expressed in USD per mmol. These scores
can be used as standalone annotations or integrated with other metrics such
as docking affinity, synthetic accessibility, or pharmacokinetic properties
to guide compound prioritization.

Because the predictions are based on a learned model, they reflect pricing
trends observed in commercial chemical suppliers and can capture nonlinear
relationships between structure and cost. However, they should be interpreted
as estimates rather than guaranteed quotes, and are best used for early-stage
filtering and comparison.

In summary, the CoPriNet protocol provides a fast, automated, and scalable
way to assess the likely commercial price of chemical compounds. It supports
structure-based workflows where compound cost is a relevant constraint, and
it integrates seamlessly with other tools in the Scipion-Chem ecosystem for
multi-criteria decision making in drug discovery.
    
    """
    
    _label = 'CoPriNet'
    
    def __init__(self, **kwargs):
        EMProtocol.__init__(self, **kwargs)
        self.stepsExecutionMode = STEPS_PARALLEL
        
    def _defineParams(self, form):
        form.addSection(label='Input')

        form.addParam('inputSet', PointerParam, pointerClass='SetOfSmallMolecules',
                      label='Molecule for Compound Availability Predictions', allowsNull=False,
                      help='Select the set of small molecules containing one or more molecules for compound availability prediction.')
                   
    def _insertAllSteps(self):
        self._insertFunctionStep('extractSmile')
        self._insertFunctionStep('createCSVFile')
        self._insertFunctionStep('runCoPriNet')
        self._insertFunctionStep('createOutputStep')

    def extractSmile(self):
        smiles = []
        for mol in self.inputSet.get():
            smi = self.getSMI(mol, 1)
            smiles.append(smi)
        self.smiles_list= smiles

    def getSMI(self, mol, nt):

        fnSmall = os.path.abspath(mol.getFileName())
        fnRoot, ext = os.path.splitext(os.path.basename(fnSmall))

        if ext != '.smi':
            outDir = os.path.abspath(self._getExtraPath())
            fnOut = os.path.abspath(self._getExtraPath(fnRoot + '.smi'))
            args = ' -i "{}" -of smi -o {} --outputDir {} -nt {}'.format(fnSmall, fnOut, outDir, nt)
            Plugin.runScript(self, 'rdkit_IO.py', args, env=RDKIT_DIC, cwd=outDir)    
        return self.parseSMI(fnOut)
        
    def parseSMI(self, smiFile):
        smi = None
        with open(smiFile) as f:
            for line in f:
                smi = line.split()[0].strip()
                if not smi.lower() == 'smiles':
                    break
        return smi
    
    def createCSVFile(self):
        csv_file_path = self._getExtraPath("test.csv")
        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = ['SMILES']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for smi in self.smiles_list:
                writer.writerow({'SMILES': smi})   
        print(f"CSV file with SMILES created at: {csv_file_path}")
    
    def runCoPriNet(self):
        fnCsv = self._getExtraPath()
        fnCsv= os.path.abspath(fnCsv)
        csv_file_path = self._getExtraPath("test.csv")
        csv_file_absolute=os.path.abspath(csv_file_path)
        program = 'python -m pricePrediction.predict'
        args = f'{csv_file_absolute} -o {fnCsv}/results.csv'
        Plugin.runCoPriNet(program, args)
        print("Predictions results saved as results.csv")

    def createOutputStep(self):
        extracted_data=[]
        csv_path = self._getExtraPath("results.csv")
        with open(csv_path, 'r') as file:
            next(file)
            for line in file:
                parts = line.strip().split(',')
                if len(parts) > 1:
                    data_after_comma = ','.join(parts[1:])
                    if not data_after_comma.strip():
                        extracted_data.append(0)
                    else:
                        extracted_data.append(data_after_comma)
                else:
                    extracted_data.append(0)

        outputSmallMolecules = SetOfSmallMolecules().create(outputPath=self._getPath(), suffix='outputSmallMolecules')
        i=0
        for mol in self.inputSet.get():
            fnSmall = os.path.abspath(mol.getFileName())
            smi = self.getSMI(mol, 1)
            cid= self.getCIDFromSmiles(smi)
            name=self.getMainNameFromCID(cid)
            if name == None:
                moleculeName=f"{smi}"
            else: 
                moleculeName=f"{name}"
            smallMolecule = SmallMolecule(smallMolFilename=os.path.relpath(fnSmall), molName=moleculeName)
            smallMolecule.CoPriNet_Price_Prediction= pwobj.Float(extracted_data[i])
            i+=1
            outputSmallMolecules.append(smallMolecule)

        outputSmallMolecules.updateMolClass()
        self._defineOutputs(outputSmallMolecules=outputSmallMolecules)


    def getCIDFromSmiles(self, smi):
        url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/%s/cids/TXT" % smi
        try:
            with urlopen(url) as response:
                cid = response.read().decode('utf-8').split()[0]
        except Exception as e:
            cid = None
        return cid
     
    def getMainNameFromCID(self,cid):
        url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{}/synonyms/TXT".format(cid)
        try:
            with urlopen(url) as response:
                r = response.read().decode('utf-8')
                synonyms = r.strip().split('\n')
                
                if synonyms:
                    main_name = synonyms[0].strip()
                else:
                    main_name = None
                
        except Exception as e:
            main_name = None
        
        return main_name
