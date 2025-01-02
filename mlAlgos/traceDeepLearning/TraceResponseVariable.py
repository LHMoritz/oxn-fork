
import pandas as pd

class TraceResponseVariable:

     def __init__(self, data : pd.DataFrame, experiment_id : str, service_name):
          self.data = data
          self.experiment_id = experiment_id
          self.service_name = service_name
          # format [traceID, flattened out weighted and normalized adj matrix, service_name (response variable name), one hot encoding for fault injection]
          self.adf_matrices : pd.DateFrame = None 

     
     

