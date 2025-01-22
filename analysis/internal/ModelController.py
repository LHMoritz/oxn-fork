
from TraceResponseVariable import TraceResponseVariable
import constants
from utils import gen_one_hot_encoding_col_names, build_colum_names_for_adf_mat_df , get_index_for_service_label
import torch
import torch.nn as nn
from TraceModel import TraceModel
from analysis.internal.TraceVariableDatasetInference import TraceVariableDatasetInference
import numpy as np
from torcheval.metrics import MulticlassPrecision , MulticlassF1Score , MulticlassRecall
from StorageClient import LocalStorageHandler
import pandas as pd



class ModelController:

     def __init__(self, variables : list[TraceResponseVariable], experiment_id : str , model :TraceModel, experiment_label : str, local_storage_handler : LocalStorageHandler):
          self.variables = variables
          self.experiment_id = experiment_id
          self.model : TraceModel = model
          # goody trace is a class itself
          self.num_classes = len(constants.SERVICES) + 1
          self.one_hot_labels = gen_one_hot_encoding_col_names()
          self.input_labels = build_colum_names_for_adf_mat_df()
          self.index_of_actual_label : int  = get_index_for_service_label(experiment_label)
          self.storage_handler : LocalStorageHandler = local_storage_handler


     '''
     This function actually puts the transformed data through the model: It does the inference part.
     '''
     def _infer_variable(self, variable : TraceResponseVariable) -> None:
          if variable.adf_matrices is not None:
               variable_dataset = TraceVariableDatasetInference(variable.adf_matrices,  self.one_hot_labels, self.input_labels)
               predicted_labels = []
               actual_lables = [self.index_of_actual_label] * len(variable.adf_matrices)
               print(len(variable.adf_matrices))
               for x in range(len(variable.adf_matrices)):
                    input , _ = variable_dataset[x]
                    output = self.model.infer(input)
                    max_index = torch.argmax(output)
                    predicted_labels.append(max_index)

               variable.predictions = torch.tensor(predicted_labels)
          #variable.confusion_matrix = multiclass_confusion_matrix(torch.Tensor(predicted_labels), torch.Tensor(actual_lables), self.num_classes).numpy()
     

     def evaluate_variables(self) -> tuple[dict[str, list[dict[str, float]]], dict[str, list[dict[str, float]]]]:
          print("starting tom evaluate varibales")
          for var in self.variables:
               print(f"evaluating for {var.service_name}")
               self._infer_variable(variable=var)
               self._f1_for_variable(var)
               self._recall_for_variable(var)
               self._precision_for_variable(var)
          
          prob_dict = self._save_cond_prob_to_disk()
          metric_dict = self._save_metrics_to_disk()
          return metric_dict, prob_dict

     '''
     For the next three function I will take the micro average between the classes or evaluation
     '''
     def _precision_for_variable(self, variable :TraceResponseVariable) -> None:
          if variable.adf_matrices is not None:
               actual_lables = torch.Tensor([self.index_of_actual_label] * len(variable.adf_matrices))
               metric = MulticlassPrecision(average="micro", num_classes=self.num_classes)
               metric.update(variable.predictions, actual_lables)
               variable.micro_precision = metric.compute().item()


     def _recall_for_variable(self, variable : TraceResponseVariable) -> None:
          if variable.adf_matrices is not None:
               actual_lables = torch.Tensor([self.index_of_actual_label] * len(variable.adf_matrices))
               metric = MulticlassRecall(average="micro", num_classes=self.num_classes)
               metric.update(variable.predictions, actual_lables)
               variable.micro_recall = metric.compute().item()

     def _f1_for_variable(self, variable: TraceResponseVariable) -> None:
          if variable.adf_matrices is not None: 
               actual_lables = torch.Tensor([self.index_of_actual_label] * len(variable.adf_matrices))
               metric = MulticlassF1Score(average="micro", num_classes=self.num_classes)
               metric.update(variable.predictions, actual_lables)
               variable.micro_f1_score = metric.compute().item()

     def _get_highest_misclassification(self, variable : TraceResponseVariable) -> None:
          pass

     # TODO be careful with the filehandling
     def _save_metrics_to_disk(self) -> dict[str, list[dict[str, float]]]:
          metric_dict = {}
          for var in self.variables:
               variable_dict = {}
               for metric in constants.METRICS:
                    variable_dict[metric] = getattr(var, metric)
               metric_dict[var.service_name] = variable_dict
          
          self.storage_handler.write_json_to_directory(f"metrics_all_variables_{self.experiment_id}", metric_dict )
          return metric_dict
     
     def _save_cond_prob_to_disk(self) -> dict[str, list[dict[str, float]]]:
          prob_dict = {}
          for var in self.variables:
               prob_dict[var.service_name] = var.error_ratio

          self.storage_handler.write_json_to_directory(f"prob_all_variables{self.experiment_id}", prob_dict)
          return prob_dict






                    





          