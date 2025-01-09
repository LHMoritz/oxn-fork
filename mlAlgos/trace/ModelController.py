from TraceResponseVariable import TraceResponseVariable
import pandas as pd
import constants
import numpy as np
import torch
import os
import torch.nn as nn
from TraceModel import TraceModel


class ModelController:

     def __init__(self, variables : list[TraceResponseVariable], experiment_id : str , model_path :str):
          self.variables = variables
          self.experiment_id = experiment_id
          self.model = self._load_model(model_path, TraceModel(nn.CrossEntropyLoss(), constants.MODEL_DIMENSIONS,  nn.ReLU()))
          # goody trace is a class itself
          self.num_classes = len(constants.SERVICES) + 1
     

     def _load_model(self, PATH : str, model : nn.Module) -> None:
          state_dict = torch.load(PATH)
          model.load_state_dict(state_dict)
          # set the model to Evaluation mode to infer on unseen data
          model.eval()
          return model


     def _calc_accuracy_for_variable(self, variable : TraceResponseVariable) -> float:
          pass

     def _calc_some_metric_for_varibable(self, variable : TraceResponseVariable) -> float:
          pass

     def _eval_variable(self, variable : TraceResponseVariable) -> torch.tensor:
          pass

     def _save_metric_to_disk(self, metric_name : str) -> None:
          pass




          