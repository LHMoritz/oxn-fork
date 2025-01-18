from TraceResponseVariable import TraceResponseVariable
import constants
from utils import gen_one_hot_encoding_col_names, build_colum_names_for_adf_mat_df
import torch
import torch.nn as nn
from TraceModel import TraceModel
from TraceVariableDataset import TraceVariableDataset
from torcheval.metrics.functional import multiclass_confusion_matrix
import numpy as np
from torcheval.metrics import MulticlassPrecision , MulticlassF1Score , MulticlassRecall
from StorageClient import LocalStorageHandler
from ModelSingleton import ModelSingleton
import pandas as pd

class ModelController:

     def __init__(self, variables : list[TraceResponseVariable], experiment_id : str , model_path :str, index_actual_MS : int, local_storage_handler : LocalStorageHandler):
          self.variables = variables
          self.experiment_id = experiment_id
          self.model : TraceModel = ModelSingleton.instance()
          # goody trace is a class itself
          self.num_classes = len(constants.SERVICES) + 1
          self.one_hot_labels = gen_one_hot_encoding_col_names()
          self.input_labels = build_colum_names_for_adf_mat_df()
          self.index_of_actual_label : int  = index_actual_MS
          self.storage_handler : LocalStorageHandler = local_storage_handler
          print(self.one_hot_labels)
          print(self.input_labels)

     # trained with 16 out
     def _load_model(self, PATH : str, model : nn.Module) -> nn.Module:
          state_dict = torch.load(PATH, weights_only=True)
          model.load_state_dict(state_dict)
          # set the model to Evaluation mode to infer on unseen data
          model.eval()
          return model

     '''
     This function actually puts the transformed data through the model: It does the inference part.
     '''
     def _infer_variable(self, variable : TraceResponseVariable) -> None:
          variable_dataset = TraceVariableDataset(variable.adf_matrices,  self.one_hot_labels, self.input_labels)
          predicted_labels = []
          actual_lables = [self.index_of_actual_label] * len(variable.adf_matrices)
          print(len(variable.adf_matrices))
          for x in range(len(variable.adf_matrices)):
               input , _ = variable_dataset[x]
               output = self.model.infer(input)
               max_index = torch.argmax(output)
               predicted_labels.append(max_index)

          variable.predictions = torch.Tensor(predicted_labels)
          #variable.confusion_matrix = multiclass_confusion_matrix(torch.Tensor(predicted_labels), torch.Tensor(actual_lables), self.num_classes).numpy()
     

     def evaluate_variables(self):
          print("starting tom evaluate varibales")
          for var in self.variables:
               print(f"evaluating for {var.service_name}")
               self._infer_variable(variable=var)
               self._f1_for_variable(var)
               self._recall_for_variable(var)
               self._precision_for_variable(var)

     '''
     For the next three function I will take the micro average between the classes or evaluation
     '''
     def _precision_for_variable(self, variable :TraceResponseVariable) -> None:
          actual_lables = torch.Tensor([self.index_of_actual_label] * len(variable.adf_matrices))
          metric = MulticlassPrecision(average="micro", num_classes=self.num_classes)
          metric.update(variable.predictions, actual_lables)
          variable.micro_precision = metric.compute().item()


     def _recall_for_variable(self, variable : TraceResponseVariable) -> None:
          actual_lables = torch.Tensor([self.index_of_actual_label] * len(variable.adf_matrices))
          metric = MulticlassRecall(average="micro", num_classes=self.num_classes)
          metric.update(variable.predictions, actual_lables)
          variable.micro_recall = metric.compute().item()

     def _f1_for_variable(self, variable: TraceResponseVariable) -> None:
          actual_lables = torch.Tensor([self.index_of_actual_label] * len(variable.adf_matrices))
          metric = MulticlassF1Score(average="micro", num_classes=self.num_classes)
          metric.update(variable.predictions, actual_lables)
          variable.micro_f1_score = metric.compute().item()

     def _get_highest_misclassification(self, variable : TraceResponseVariable) -> None:
          pass

     # TODO be careful with the filehandling
     def _save_metrics_to_disk(self) -> None:
          metric_dict = {}
          for var in self.variables:
               variable_dict = {}
               for metric in constants.METRICS:
                    variable_dict[metric] = getattr(var, metric)
               metric_dict[var.service_name] = variable_dict
          
          self.storage_handler.write_json_to_directory(constants.ANALYSIS_DIR, constants.VARIABLE_METRICS, metric_dict)
     
     def _save_cond_prob_to_disk(self) -> None:
          prob_dict = {}
          for var in self.variables:
               prob_dict[var.service_name] = var.error_ratio

          self.storage_handler.write_json_to_directory(constants.ANALYSIS_DIR, constants.VARIABLE_PROBS)     


                    





          