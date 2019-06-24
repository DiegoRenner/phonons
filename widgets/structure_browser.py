from aiida.orm.querybuilder import QueryBuilder
from aiida.orm.data.structure import StructureData
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.calculation.work import WorkCalculation
from aiida.orm import Node
    
from collections import OrderedDict
import ipywidgets as ipw
import datetime
import os.path


class StructureBrowser(ipw.VBox):
    
    def __init__(self):
       
        layout = ipw.Layout(width="900px")
        max_mode = 0
        modes_options = range(0,max_mode)
        # Date range
        self.dt_now = datetime.datetime.now()
        self.dt_end = self.dt_now - datetime.timedelta(days=10)
        self.date_start = ipw.Text(value='',
                                   description='From: ',
                                   style={'description_width': '120px'})

        self.date_end = ipw.Text(value='',
                                 description='To: ')

        self.date_text = ipw.HTML(value='<p>Select the date range:</p>')
        
        self.btn_date = ipw.Button(description='Search',
                                   layout={'margin': '1em 0 0 0'})

        self.age_selection = ipw.VBox([self.date_text, ipw.HBox([self.date_start, self.date_end]), self.btn_date],
                                      layout={'border': '1px solid #fafafa', 'padding': '1em'})

        self.btn_date.on_click(self.search)
        
        hr = ipw.HTML('<hr>')
        box = ipw.VBox([self.age_selection,
                        hr])
        
        self.results = ipw.Dropdown(layout=layout)
        self.modes = ipw.Dropdown(layout=layout)
        self.search()
        super(StructureBrowser, self).__init__([box, hr, self.results,self.modes])
    
    
    def preprocess(self):
        qb = QueryBuilder()
        qb.append(StructureData, filters={'extras': {'!has_key': 'formula'}})
        for n in qb.all(): # iterall() would interfere with set_extra()
            formula = n[0].get_formula()
            n[0].set_extra("formula", formula)

    
    def search(self, c=None):
        try: # If the date range is valid, use it for the search
            self.start_date = datetime.datetime.strptime(self.date_start.value, '%Y-%m-%d')
            self.end_date = datetime.datetime.strptime(self.date_end.value, '%Y-%m-%d') + datetime.timedelta(hours=24)
        except ValueError: # Otherwise revert to the standard (i.e. last 7 days)
            self.start_date = self.dt_end
            self.end_date = self.dt_now + datetime.timedelta(hours=24)

            self.date_start.value = self.start_date.strftime('%Y-%m-%d')
            self.date_end.value = self.end_date.strftime('%Y-%m-%d')
        
        qb = QueryBuilder()
        qb.append(Node, filters={'type': 'data.folder.FolderData.', 'ctime':{'and':[{'<=': self.end_date},{'>': self.start_date}]}}, tag='output')
        qb.append(Node,filters={'label': 'phonons_opt'}, input_of='output')
        

        #qb.order_by({StructureData:{'ctime':'desc'}})
        matches = set([n[0] for n in qb.iterall()])
        matches = sorted(matches, reverse=True, key=lambda n: n.ctime)
        
        c = len(matches)
        options = OrderedDict()
        options["Select a Structure"] = 'False'

        for n in matches:
            file_path = n.out.retrieved.folder.abspath + "/path/aiida-VIBRATIONS-1.mol"
            if os.path.isfile(file_path):
                    label  = "PK: %d" % n.pk
                    label += " | " + n.ctime.strftime("%Y-%m-%d %H:%M")
                    options[label] = n

        self.results.options = options
        
    def set_modes(self,max_modes=100,c=None):
        options = OrderedDict()
        options["Select a Mode (%d found)"%max_modes] = 'False'
        for i in range(0,max_modes):
            label = 'Mode # %d' % i
            options[label] = i
        self.modes.options = options
        
        
        
        
        
        
        
        
        
        
        
        