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

    AI Generated:

        ProtChemCoPriNet - User Manual

        Overview
        --------
        The ProtChemCoPriNet protocol predicts the likely commercial price of small
        molecules using a graph neural network model trained on real-world pricing
        data. It provides an estimate of compound cost based solely on chemical
        structure, enabling users to integrate economic feasibility into compound
        selection workflows.

        This protocol is particularly useful in early-stage drug discovery, where
        prioritizing compounds by both biological activity and predicted cost can
        help streamline decision-making.

        Input Requirements
        ------------------
        1. **Molecule Set**:
           - A `SetOfSmallMolecules` object containing the compounds to analyze.
           - Supported file formats include SDF, MOL, or SMILES files.

        Workflow
        --------
        1. **SMILES extraction**:
           - Each molecule in the input set is converted to a SMILES representation.
           - RDKit is used to handle format conversion if needed.

        2. **CSV preparation**:
           - A CSV file (`test.csv`) is generated with a column of SMILES strings,
             which serves as input to the CoPriNet model.

        3. **Run CoPriNet**:
           - The CoPriNet Python module (`pricePrediction.predict`) is executed
             using the prepared CSV file.
           - Predictions are written to a results CSV (`results.csv`).

        4. **Output processing**:
           - Predicted prices are extracted from the results CSV.
           - Each molecule is associated with its predicted price in a
             `SetOfSmallMolecules` output object.
           - Optional: retrieve compound CID and main name from PubChem for better
             annotation.

        Outputs
        -------
        - **results.csv**:
          - Contains predicted prices for each molecule.
          - Prices are expressed in USD per mmol (estimated values).

        - **SetOfSmallMolecules output**:
          - Each `SmallMolecule` object includes:
            - `CoPriNet_Price_Prediction`: predicted price.
            - `molName`: compound name derived from PubChem if available; otherwise SMILES.

        Validation & Warnings
        ---------------------
        - Input molecules must be valid and parseable; invalid structures may
          cause errors during SMILES conversion.
        - Internet connection is required to query PubChem for compound IDs
          and names.
        - Predicted prices are estimates based on training data and should
          not be considered guaranteed quotes.
        - Ensure the CoPriNet module is correctly installed and accessible in
          the Python environment.

        Practical Recommendations
        -------------------------
        - Use this protocol to filter compounds by predicted cost in combination
          with other metrics (docking scores, synthetic accessibility, etc.).
        - Verify SMILES correctness if unexpected results occur.
        - The pipeline is parallelized; large datasets can be processed efficiently.

        Final Perspective
        -----------------
        ProtChemCoPriNet provides an automated and scalable approach to estimate
        compound pricing based on chemical structure. By integrating predicted
        cost into compound prioritization, users can make more informed
        decisions in computational drug discovery workflows.
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
