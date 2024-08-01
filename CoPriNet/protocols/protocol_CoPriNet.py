################ VERÓNICA GAMO PAREJO ##############################

# General imports 
import os
import csv
import pandas as pd 

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

    """ CoPriNet"""
    
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

        csv_path = self._getExtraPath("results.csv")
        scores_df = pd.read_csv(csv_path, sep=',')

        outputSmallMolecules = SetOfSmallMolecules().create(outputPath=self._getPath(), suffix='outputSmallMolecules')

        for mol in self.inputSet.get():
            fnSmall = os.path.abspath(mol.getFileName())
            smi = self.getSMI(mol, 1)
            
            row = scores_df[scores_df['SMILES'] == smi]
            if not row.empty:
                cid= self.getCIDFromSmiles(smi)
                name=self.getMainNameFromCID(cid)
                if name == None:
                    moleculeName=f"{smi}"
                else: 
                    moleculeName=f"{name}"
                smallMolecule = SmallMolecule(smallMolFilename=os.path.relpath(fnSmall), molName=moleculeName)
                smallMolecule.CoPriNet_Price_Prediction= pwobj.Float(row['CoPriNet'].values[0])


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
