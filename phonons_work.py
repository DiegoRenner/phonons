from aiida.orm.data.structure import StructureData
from aiida.orm.data.parameter import ParameterData
from aiida.orm.data.remote import RemoteData
from aiida.orm.data.folder import FolderData
from aiida.orm.data.base import Int, Float, Str, Bool
from aiida.orm.data.singlefile import SinglefileData
from aiida.orm.code import Code

from aiida.work.workchain import WorkChain, ToContext, Calc, while_
from aiida.work.run import submit

from aiida_cp2k.calculations import Cp2kCalculation

import tempfile
import shutil
import itertools
import numpy as np

from ase.data import covalent_radii
from ase.neighborlist import NeighborList
from ase import Atoms
from io import StringIO, BytesIO

from apps.phonons.get_cp2k_input_dev import Get_CP2K_Input
from apps.surfaces.widgets import find_mol

class PhononsWorkchain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(PhononsWorkchain, cls).define(spec)
        
        spec.input('parameters', valid_type    = ParameterData)
        spec.input('code'      , valid_type    = Code)
        spec.input('structure' , valid_type    = StructureData)
        spec.input('parent_folder', valid_type = RemoteData, default=None, required=False)
        
        spec.outline(
            #cls.print_test,
            cls.run_phonons #,
#            while_(cls.not_converged)(
#                cls.run_gw_again
#            ),
        )
        spec.dynamic_output()

    # ==========================================================================
    def not_converged(self):
        return self.ctx.gw_opt.res.exceeded_walltime
    # ==========================================================================
    def print_test(self):
        self.report("Reporting test")
        self.report("cell_str: %s %s" % (self.inputs.cell_str, str(self.inputs.cell_str)))

    # ==========================================================================
    def run_phonons(self):
        self.report("Running CP2K GW")
        
        parameters_dict = self.inputs.parameters.get_dict()
        inputs = self.build_calc_inputs(code           = self.inputs.code,
                                        parent_folder  = None,
                                        structure      = self.inputs.structure,
                                        input_dict     = parameters_dict )

        self.report("inputs: "+str(inputs))
        self.report("parameters: "+str(inputs['parameters'].get_dict()))
        self.report("settings: "+str(inputs['settings'].get_dict()))
        
        future = submit(Cp2kCalculation.process(), **inputs)
        return ToContext(phonons_opt=Calc(future))

    # ==========================================================================
#    def run_gw_again(self):
#        # TODO: make this nicer.
#        the_dict = self.inputs.input_dict.get_dict()
#        the_dict['parent_folder'] = self.ctx.gw_opt.out.remote_folder
#        inputs_new = self.build_calc_inputs(input_dict=the_dict)
#        
#
#        self.report("inputs (restart): "+str(inputs_new))
#        future_new = submit(Cp2kCalculation.process(), **inputs_new)
#        return ToContext(gw_opt=Calc(future_new))

    # ==========================================================================
    @classmethod
    def build_calc_inputs(cls,
                          code          = None,
                          parent_folder = None,
                          structure     = None,
                          input_dict    = None):

        inputs = {}
        inputs['_label'] = "phonons_opt"
        inputs['code'] = code
        inputs['file'] = {}

 
        atoms = structure.get_ase()# slow
        input_dict['atoms'] = atoms
        
        basis_f = SinglefileData(file='/project/apps/surfaces/Files/RI_HFX_BASIS_all')
        inputs['file']['ri_hfx_basis_all'] = basis_f
        
        
        molslab_f = cls.mk_aiida_file(atoms, "mol_on_slab.xyz")
        inputs['file']['molslab_coords'] = molslab_f
        first_slab_atom = None
        calc_type = input_dict['calc_type']
        
        if calc_type != 'Full DFT':
            
            # Au potential
            pot_f = SinglefileData(file='/project/apps/surfaces/slab/Au.pot')
            inputs['file']['au_pot'] = pot_f
            tipii = find_mol.get_types(atoms,0.1)
            mol_atoms = np.where(tipii==0)[0].tolist()
            #mol_indexes = find_mol.molecules(mol_atoms,atoms)
            #print(atoms[mol_indexes])
            #print(mol_indexes)
            first_slab_atom = len(mol_atoms) + 1
            mol_f = cls.mk_aiida_file(atoms[mol_atoms], "mol.xyz")
            inputs['file']['mol_coords'] = mol_f
            
            if calc_type == 'Mixed DFTB':
                walltime = 18000
        
        # parameters
        cell_ase = atoms.cell.flatten().tolist()
        
        
        if 'cell' in input_dict.keys():
            if input_dict['cell'] == '' or input_dict['cell'] == None :
                input_dict['cell'] = cell_ase   
            else:
                cell_abc=input_dict['cell'].split()
                input_dict['cell']=np.diag(np.array(cell_abc, dtype=float)).flatten().tolist()
        else:
            input_dict['cell'] = cell_ase

#        remote_computer = code.get_remote_computer()
#        machine_cores = remote_computer.get_default_mpiprocs_per_machine()
     
        #inp =     get_cp2k_input(input_dict = input_dict)
        input_dict['machine_cores'] = input_dict['nproc_rep']*input_dict['nreplicas']
        input_dict['first_slab_atom'] = first_slab_atom
        input_dict['last_slab_atom'] = len(atoms)
        
        inp = Get_CP2K_Input(input_dict = input_dict).inp                         
        

        if 'parent_folder' in input_dict.keys():
            inp['EXT_RESTART'] = {
                'RESTART_FILE_NAME': './parent_calc/aiida-1.restart'
            }
            inputs['parent_folder'] = input_dict['remote_calc_folder']

        inputs['parameters'] = ParameterData(dict=inp)
        
        # settings
        settings = ParameterData(dict={'additional_retrieve_list': ['*.mol_vib']})
        inputs['settings'] = settings

        # resources
        inputs['_options'] = {
            'resources' : {'num_machines'             : input_dict['num_machines'],
                           'num_mpiprocs_per_machine' : input_dict['proc_node'],
                           'num_cores_per_mpiproc'    : input_dict['num_cores_per_mpiproc']
                          },
            'max_wallclock_seconds': int(input_dict['walltime']),
        }

        return inputs
    
    # ==========================================================================
    @classmethod
    def mk_aiida_file(cls, atoms, name):
        tmpdir = tempfile.mkdtemp()
        atoms_file_name = tmpdir + "/" + name
        atoms.write(atoms_file_name)
        atoms_aiida_f = SinglefileData(file=atoms_file_name)
        shutil.rmtree(tmpdir)
        return atoms_aiida_f
        

    # ==========================================================================
    def _check_prev_calc(self, prev_calc):
        error = None
        if prev_calc.get_state() != 'FINISHED':
            error = "Previous calculation in state: "+prev_calc.get_state()
        elif "aiida.out" not in prev_calc.out.retrieved.get_folder_list():
            error = "Previous calculation did not retrive aiida.out"
        else:
            fn = prev_calc.out.retrieved.get_abs_path("aiida.out")
            content = open(fn).read()
            if "exceeded requested execution time" in content:
                error = "Previous calculation's aiida.out exceeded walltime"

        if error:
            self.report("ERROR: "+error)
            self.abort(msg=error)
            raise Exception(error)

# EOF
