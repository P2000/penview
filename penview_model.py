# encoding: utf-8
from itertools import count

from data_access import ExperimentFile
    
class OpenExperiment:
    def __init__(self, path):
        """initialize Experiment: load values and metadata table into classvariables
                  :Parameters:
            path  file-path"""
        self.experiment_perspective = None
        e = ExperimentFile(path)
        self.values = e.load_values()
        self.metadata = e.load_metadata()

    def get_actor_name(self):
        """return actor_name from metadata-table"""
        actor_name = self.metadata['actor_name']
        return actor_name

    def get_date(self):
        """return date unformatted from metadata-table"""
        date = self.metadata['date']
        return date
    
    def get_exp_name(self):
        exp_name = self.metadata['exp_name']
        return exp_name
    
    #TODO: in view auslagern!
    def get_details_text(self):
        """return actor_name, date and ev. additional_details from metadata-table"""
        #Durchgeführt von: Namen
        actor_name = self.get_actor_name()
        details_text =  "Durchgeführt von %s" % actor_name
        #Datum
        date = self.get_date()
        details_text += "\nDatum, %s" % date
        try:
            #Konstante (z.b. Federkonstante)
            additional_info = self.metadata['additional_info']
            details_text += "\n%s" % additional_info
        except:
            pass
        return details_text
        
    def get_values(self):
        """return a list of all values from values-table"""
        return self.values
        
    def get_time_values(self):
        """return list of time values from values-table"""
        time_values = []
        for i in range(len(self.values)):
            time_values.append(self.values[i][0])
        return time_values
        
    def get_nvalues(self):
        """return the number of values (v1, v2, v3, v4 -> 4) in table 'values' """
        print "self.values[0]:" + str(self.values[0])
        nvalues = len(self.values[0])-1
        return nvalues
        
    def get_desc(self):
        """return a list of vn_desc (v1, v2..)"""
        desc = []
        print "nvalues: %s " % self.get_nvalues()
        for i in range(self.get_nvalues()):
            key = 'v' + str(i+1) + '_desc'
            print "key: %s" % key
            desc.append(self.metadata[key])
        return desc

class ExperimentPerspective:
    def __init__(self):
        """ Initialize Perspective
        
        """
        self.values_upd = [] # list of scaling factor for ALL values 
        self.xaxis_values = 0 # index of current xaxis values
        self.yaxis_values = [] # list of indices of values visible on yaxis

class RecentExperiment:
    def __init__(self):
        self.name = None
        self.path = None

class PenViewConf:
    ox_ids = count()
    def __init__(self):
        self.listeners = []         # list of listener functions taking one argument: the conf that was updated
        self.open_experiments = []      # list of OpenExperiment objects - the experiments currently opened  
        self.recent_experiments = []        # list of RecentExperiment objects - maximNoneum size 5, fifo semantics    

    def add_open_experiment(self, ox):
        ox.id = PenViewConf.ox_ids.next()
        self.open_experiments.append(ox)
        for update in self.listeners:
            update(self)

    def add_listener(self, listener):
        self.listeners.append(listener)

    def set_controller(self, controller):
        self.controller = controller
    
#a = OpenExperiment('examples/abklingkonstante.sqlite')
#print a.values
#print a.metadata
#print a.get_details_text()
#print a.get_time_values()
#print a.get_nvalues()
#print a.get_desc()
