
from analysis.internal.TraceResponseVariable import TraceResponseVariable
import analysis.internal.constants as constants
from analysis.internal.utils import gen_one_hot_encoding_col_names, build_colum_names_for_adf_mat_df , get_index_for_service_label
import torch
from analysis.internal.TraceModel import TraceModel
from analysis.internal.TraceVariableDatasetInference import TraceVariableDatasetInference
from torcheval.metrics import MulticlassPrecision , MulticlassF1Score , MulticlassRecall
from analysis.internal.StorageClient import LocalStorageHandler
import logging

logger = logging.getLogger(__name__)

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
               #actual_lables = [self.index_of_actual_label] * len(variable.adf_matrices)
               for x in range(len(variable.adf_matrices)):
                    input , _ = variable_dataset[x]
                    output = self.model.infer(input)
                    max_index = torch.argmax(output)
                    predicted_labels.append(max_index)

               variable.predictions = torch.tensor(predicted_labels)
     

     def evaluate_variables(self) -> tuple[dict[str, list[dict[str, float]]], dict[str, list[dict[str, float]]], dict[str, float]]:
               logger.info("starting to infer and evaluate variables")
 
               for var in self.variables:
                    try:
                         logger.info(f"evaluating for {var.service_name}")
                         self._infer_variable(variable=var)
                         self._f1_for_variable(var)
                         self._recall_for_variable(var)
                         self._precision_for_variable(var)
                    except Exception as e:
                         logger.error(f"Error in evaluation the variable: {var.service_name} : {str(e)}")
               
               aggregation = self.aggregate_over_the_experiment()
               metrics = self._get_metrics()
               probs = self._get_probs()
               return metrics , probs, aggregation
    
     
     def _get_metrics(self) -> dict[str, list[dict[str, float]]]:
          logger.info(f"getting the metrics for the experiment with id : {self.experiment_id}")
          metrics = {}
          for var in self.variables:
               metrics_for_var = {}
               if var.micro_f1_score is not None:
                    metrics_for_var["micro_f1_score"] = var.micro_f1_score
               if var.micro_precision is not None:
                    metrics_for_var["micro_precision"] = var.micro_precision
               if var.micro_recall is not None:
                    metrics_for_var["micro_recall"] = var.micro_recall
               
               if len(metrics_for_var) > 0:
                    metrics[var.service_name] = metrics_for_var
          
          return metrics

     def _get_probs(self) -> dict[str, list[dict[str, float]]]:
          logger.info(f"getting the probs for the experiment with id : {self.experiment_id}")
          probs = {}
          for var in self.variables:
               if len(var.error_ratio) > 0:
                    probs[var.service_name] = var.error_ratio
          
          return probs
     
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

     
     """
          Here I am doing a weighted average over all the  the results.
          The weights will be the length of the raw data of the response varibales.
     """
     def aggregate_over_the_experiment(self) -> dict[str, float]:

          logger.info(f"starting aggregation for experiment with id : {self.experiment_id}")

          aggregations = {}
          lengths , sum  = self.get_lengths_response_variables()

          nominator_precision = 0
          nominator_recall = 0
          nominator_f1 = 0
          for var in self.variables:
               if var.micro_f1_score is not None:
                    nominator_f1 += lengths[var.service_name] * var.micro_f1_score
               if var.micro_precision is not None:
                    nominator_precision += lengths[var.service_name] * var.micro_precision
               if var.micro_recall is not None:
                    nominator_recall += lengths[var.service_name] * var.micro_recall
          
          if sum == 0:
               aggregations["micro_precision_agg"] = -1
               aggregations["micro_recall_agg"] = -1
               aggregations["micro_f1_score_agg"] = -1
          else:
               aggregations["micro_precision_agg"] = nominator_precision / sum
               aggregations["micro_recall_agg"] = nominator_recall / sum
               aggregations["micro_f1_score_agg"] =  nominator_f1 / sum
          
          return aggregations

     def get_lengths_response_variables(self) -> tuple[dict[str, int], int]:
          lenghts = {}
          sum = 0
          for var in self.variables:
               var_length = len(var.adf_matrices)
               lenghts[var.service_name] = var_length
               sum += var_length

          #logger.info(f"lenght dictionary : {lenghts}")
          #logger.info(sum)
          return lenghts, sum








                    





          