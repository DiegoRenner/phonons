from __future__ import print_function
from __future__ import absolute_import

import ipywidgets as ipw
from IPython.display import display, clear_output
from apps.surfaces.widgets.neb_utils import mk_coord_files, mk_wfn_cp_commands
from aiida.orm.code import Code
from aiida.orm import load_node
from aiida.orm import Code, Computer

###The widgets defined here assign value to the following input keywords
###stored in jod_details:
#'nreplicas'
#'replica_pks'
#'wfn_cp_commands' copied in aiida.inp to retrieve old .wfn files
#'struc_folder' used to create replica files
#'nproc_rep'
#'spring'
#'nstepsit'
#'endpoints'
#'rotate'
#'align'


style = {'description_width': '120px'}
layout = {'width': '70%'}
layout3 = {'width': '23%'}

class PHNSDetails(ipw.VBox):
    def __init__(self,job_details={},  **kwargs):
        """ Dropdown for DFT details
        """
        ### ---------------------------------------------------------
        ### Define all child widgets contained in this composite widget
        
        self.job_details=job_details
        
        self.proc_node = ipw.IntText(value=job_details['proc_node'],
                           description='# Processors per Node',
                           style=style, layout=layout)

        self.proc_rep = ipw.IntText(value=job_details['nproc_rep'],
                           description='# Processors per replica',
                           style=style, layout=layout)  
        
        self.num_rep = ipw.IntText(value=job_details['nreplicas'],
                           description='# Replicas',
                           style=style, layout=layout)
        
        
        
        
        
        ### ---------------------------------------------------------
        ### Logic

        
        
        update_jd_widgets = [
            self.proc_node, self.proc_rep, self.num_rep
        ]
        for w in update_jd_widgets:
            w.observe(lambda v: self.update_job_details(), 'value')
        
        self.neb_out = ipw.Output()
        ### ---------------------------------------------------------
        ### Define the ipw structure and create parent VBOX

        children = [
            self.proc_node,
            self.proc_rep, 
            self.num_rep,
            self.neb_out
        ]
            
        super(PHNSDetails, self).__init__(children=children, **kwargs)
        
    ####TO DO decide how to deal with UPDATE VS WFN retrieve           
    def update_job_details(self):
        
        self.job_details['proc_node']=self.proc_node.value     
        self.job_details['nproc_rep']=self.proc_rep.value
        self.job_details['nreplicas']=self.num_rep.value
        
        

    def reset(self, proc_node=1, proc_rep=12, num_rep=1, num_calcs=6000):  
        
        self.nodes_geopt.value = proc_node
        self.proc_rep.value = proc_rep
        self.num_rep.value = num_rep
        
        #self.job_details={}
        self.update_job_details()
        


    