
import pandas as pd
import torch
from typing import Optional

class TraceResponseVariable:

     def __init__(self, data : pd.DataFrame, experiment_id : str, service_name):
          self.data = data
          self.experiment_id = experiment_id
          self.service_name = service_name
          # format [traceID, flattened out weighted and normalized adj matrix, service_name (response variable name), one hot encoding for fault injection]
          self.adf_matrices : Optional[pd.DataFrame] = None
          self.error_ratio : dict[str, float] = {}
          # good [avg, std], faulty [avg, std]
          #self.time_dis : dict[str, tuple[float, float]] = None
          self.predictions : Optional[torch.Tensor] = None
          self.micro_precision = None
          self.micro_recall = None
          self.micro_f1_score = None

     
     

