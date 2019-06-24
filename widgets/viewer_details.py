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
        self.viewer.add_ball_and_stick(aspectRatio=REST_ASPECT, opacity=1.0,component=1)
        
        self.viewer.add_unitcell()
        
    def setup(self, file_path,atoms,  mode, details=None): 
       
        a, freq, vibr_displacements = read_molden(file_path)
        trajectory = get_trajectory(mode,a, freq, vibr_displacements)
        
        viewer = nglview.show_asetraj(trajectory, gui=True)
        
        cell_z = atoms.cell[2, 2]
        com = atoms.get_center_of_mass()
        def_orientation = viewer._camera_orientation
        top_z_orientation = [1.0, 0.0, 0.0, 0,
                             0.0, 1.0, 0.0, 0,
                             0.0, 0.0, -np.max([cell_z, 30.0]) , 0,
                             -com[0], -com[1], -com[2], 1]
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
    enhance_disp = 1.0
    time_arr = np.linspace(0.0, 2*np.pi, 20)

    trajectory = []
    for time in time_arr:
        vibr_atoms = Atoms(a.get_chemical_symbols(), a.positions+enhance_disp*np.sin(time)*vibr_displacements[mode])
        trajectory.append(vibr_atoms)
    return trajectory
    
    
        
        
        
        

    