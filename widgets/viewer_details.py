from __future__ import print_function
from __future__ import absolute_import

from collections import OrderedDict
from IPython.display import display, clear_output, HTML
import matplotlib.pyplot as plt
from ase.io import read,write
from ase.visualize import view
from ase.data import vdw_radii
import nglview
import ipywidgets as ipw
from IPython.display import display, clear_output
from ase import Atoms
import numpy as np

MOL_ASPECT  = 3.0
REST_ASPECT = 10.0

class ViewerDetails(ipw.VBox):
    
    def __init__(self, **kwargs):
         
        #self.viewer = nglview.NGLWidget(gui=True)
        self.vib_viewer = ipw.Output()
        self.spec_viewer = ipw.Output()
        
        
       
        
        children = [
           self.vib_viewer,
           self.spec_viewer
        
        ]
        super(ViewerDetails, self).__init__(children=children, **kwargs)
        
   
    
        

    
    def reset(self):
        """
        Resets the representations of currently set up viewer instance
        """
            
        self.viewer.component_0.clear_representations()
        self.viewer.add_ball_and_stick(aspectRatio=MOL_ASPECT, opacity=1.0,component=0)
        
        self.viewer.component_1.clear_representations()
        self.viewer.add_ball_and_stick(aspectRatio=REST_ASPECT, opacity=1.0,component=2)
        
        self.viewer.add_unitcell()
        
    def setup(self, file_path, atoms,  mode, details=None): 
       
        a, freq, vibr_displacements = read_molden(file_path)
        trajectory_mol = get_trajectory(mode,atoms, freq, vibr_displacements)
        trajectory_slab = get_trajectory(mode,atoms, freq, vibr_displacements)
        
        if details is None:
            mol_inds = list(np.arange(0, len(atoms)))
            rest_inds = []
        else:
            mol_inds = [item for sublist in details['all_molecules'] for item in sublist]
            rest_inds = details['slabatoms']+details['bottom_H']+details['adatoms'] +details['unclassified']
        
        #trajectory_mol = trajectory
        for i in range(0,len(trajectory_mol)):
            del trajectory_mol[i][rest_inds]
            
        #trajectory_slab = trajectory
        for i in range(0,len(trajectory_slab)):
            del trajectory_slab[i][mol_inds]
        
            
            
            
        
        ase_traj_mol = nglview.ASETrajectory(trajectory_mol)
        ase_traj_slab = nglview.ASETrajectory(trajectory_slab)

        
        #viewer = nglview.show_asetraj(trajectory, gui=True)
        #viewer[0].add_representation('ball_and_stick',selection=list(np.arange(0, 46)))
        #viewer.add_component(nglview.ASEStructure(atoms), default_representation=False)
        #viewer.add_ball_and_stick(aspectRatio=MOL_ASPECT, opacity=1.0,component=1)
        
        viewer = nglview.NGLWidget(gui=True)
        viewer.add_trajectory(ase_traj_slab, default_representation=False)
        viewer.add_trajectory(ase_traj_mol, default_representation=False)
        viewer.add_representation('ball+stick',aspectRatio=REST_ASPECT, opacity=1.0,component=0)
        viewer.add_representation('ball+stick',aspectRatio=MOL_ASPECT, opacity=1.0,component=1)
        
        
        
        com = atoms.get_center_of_mass()
        cell_z = atoms.cell[2, 2]
        #top_z_orientation = [1.0, 0.0, 0.0, 0,
        #                     0.0, 1.0, 0.0, 0,
        #                     0.0, 0.0, np.max([cell_z, 30.0]) , 0,
        #                     -com[0], -com[1], -com[2], 1]
        cell_x = atoms.cell[1, 1]
        top_z_orientation = [0.0 , np.max([cell_x,40])*np.sin(np.pi*1/25), np.max([cell_x,40])*np.cos(np.pi*1/25), 0.0,
                             1.0, 0.0, 0.0, 0.0,
                             0.0 , np.max([cell_x,40])*np.cos(np.pi*1/25), -np.max([cell_x,40])*np.sin(np.pi*1/25), 0.0,
                             -com[0], -com[1], -com[2], 1.0]
        
        viewer._set_camera_orientation(top_z_orientation)
        with self.vib_viewer:
            clear_output()
            display(viewer)
        def f():
            plt.figure(figsize=(10,5))
            plt.vlines(freq,np.zeros(len(freq)),np.ones(len(freq)))
            #for i, f in enumerate(freq):
            #    print(i,f)
            plt.hlines(0,*plt.xlim())
            plt.xlabel('Energy [cm$^{-1}$]',fontsize=12)
        interactive_plot = ipw.interactive(f)
        with self.spec_viewer:
            clear_output()
            display(interactive_plot)
        
        def f():
            plt.figure(figsize=(10,5))
            plt.vlines(freq,np.zeros(len(freq)),np.ones(len(freq)))
            #for i, f in enumerate(freq):
            #    print(i,f)
            plt.hlines(0,*plt.xlim())
            plt.xlabel('Energy [cm$^{-1}$]',fontsize=12)
            




#output = interactive_plot.children[-1]
#output.layout.height = '350px'

            
        
def read_molden(file):
    
    with open(file) as f:
        data = f.readlines()

    freq = []
    info_atoms = [] # element, x, y, z
    vibr_displacements = [] # [vibration_nr][coord]

    inten = []


    section = ''
    b2A=0.52917721067
    # Parse the datafile
    for line in data:
        line = line.strip()

        # Are we entering into a new section?
        if line[0] == '[':
            section = line.strip('[]').lower()
            continue

        if section == 'freq':
            freq.append(float(line))

        if section == 'fr-coord':
            el, x, y, z = line.split()
            info_atoms.append([el, float(x)*b2A, float(y)*b2A, float(z)*b2A])

        if section == 'fr-norm-coord':
            if line.startswith('vibration'):
                vibr_displacements.append([])
                continue
            coords = [float(x) for x in line.split()]
            vibr_displacements[-1].append(coords)

        if section == 'int':
            inten.append(float(line))

    vibr_displacements = np.asanyarray(vibr_displacements)
    info_atoms = np.asanyarray(info_atoms)
    atoms = Atoms(info_atoms[:,0], info_atoms[:,1:4])

    return atoms, freq, vibr_displacements        


def get_trajectory(mode,a, freq, vibr_displacements):
    enhance_disp = 10.0
    time_arr = np.linspace(0.0, 2*np.pi, 20)
    
    trajectory = []
    for time in time_arr:
        vibr_atoms = Atoms(a.get_chemical_symbols(), a.positions+enhance_disp*np.sin(time)*vibr_displacements[mode])
        trajectory.append(vibr_atoms)
        #a.positions = a.get_positions()+enhance_disp*np.sin(time)*vibr_displacements[mode]        
        #trajectory.append(a)
        
    return trajectory
    
    
        
        
        
        

    