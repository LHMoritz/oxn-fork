from TraceResponseVariable import TraceResponseVariable
import pandas as pd
import constants
import numpy as np
import torch.nn as nn


class ModelController:

     def __init__(self, variables : list[TraceResponseVariable], experiment_id : str , model_path :str):
          self.variables = variables
          self.experiment_id = experiment_id
          self.model 
     

     def _calc_accuracy_for_variable(self):
          pass

     def _eval_variable(self, variable : TraceResponseVariable) -> torch.tensor:
          pass
          