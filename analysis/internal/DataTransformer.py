

from analysis.internal.StorageClient import LocalStorageHandler
from analysis.internal.RWDGController import RWDGController
from analysis.internal.TraceResponseVariable import TraceResponseVariable
from analysis.internal.TraceModel import TraceModel, visualize_training_precision, plot_average_precisions
import analysis.internal.constants as constants
from analysis.internal.TraceVariableDatasetInference import TraceVariableDatasetInference
from analysis.internal.utils import gen_one_hot_encoding_col_names, build_colum_names_for_adf_mat_df
from torch.utils.data import DataLoader, random_split
import os
import torch.nn as nn
import logging
import pandas as pd
import json



logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


"""
     This class is forn transforming data on disk. To actually train  the Multilayer-Perceptron.
"""
class DataTransformerAndAnalyzer():

     def __init__(self, storage_handler : LocalStorageHandler):
          self.storage_handler = storage_handler
          self.trace_model = TraceModel(nn.CrossEntropyLoss(), constants.SMALL_MODEL_DIMENSIONS
                                        ,  nn.ReLU())
     
     """
     This function transfrom the entire data in the training. I want to transform exactly 1 File at the time.
     """
     def transform_data(self, experiment_id, experiment_label : str) -> None:
          file_list = self.storage_handler.list_files_in_dir(experiment_id=experiment_id)

          for file_name in file_list:
               try:
                    tup = self.storage_handler.get_file_from_dir(file_name=file_name)
                    if tup is None:
                         logger.error(f" For experiment with ID : {experiment_id}, could not retrive data for for file : {file_name}")
                         continue

                    varibales_list : list[TraceResponseVariable] = [TraceResponseVariable(tup[0] , experiment_id , tup[1])]
                    con = RWDGController(variables=varibales_list, experiment_id=experiment_id, injected_service=experiment_label)

                    con.iterate_over_varibales()

                    con.variables[0].adf_matrices.to_csv(f"./internal/oxn/transformed/{file_name[:-5]}.csv", index=False)
                    logger.info(f"for exp: {experiment_id} and file : {file_name} data got successfully transformed and written")
               
               except Exception as e:
                    logger.error(str(e))
     
     def check_imbalanced_data(self, experiment_id : str) -> None:
          file_list = self.storage_handler.list_files_in_dir(experiment_id=experiment_id)
          data_lenghts : dict[str, int] = {}
          for file_name in file_list:
             df = pd.read_csv(f"./internal/oxn/transformed/{file_name}")
             data_lenghts[file_name] = len(df)
          try:
               with open(f"./internal/oxn/transformed/{experiment_id}_data_lenghts.json", "w") as json_file:
                    json.dump(data_lenghts, json_file, indent=4)

               logger.info("wrote data to disk")
          except Exception as e:
               logger.error(str(e))
     

     def check_goody_faulty_traces(self):
          original_path = "./internal/oxn/trainData"
          files_list = os.listdir(original_path)
          ratios : dict[str, dict[str, float]] = {}
          goodys_ratios = []
          faultys_rations = []
          for file_name in files_list:
               try:
                    df = pd.read_json(f"./internal/oxn/trainData/{file_name}")
                    if len(df) > 0:
                         no_treatments = df[df["delay_treatment"] == "NoTreatment"]
                         treatments = df[df["delay_treatment"] == "delay_treatment"]
                         goodys_ratio = len(no_treatments) / len(df)
                         faulty_ratio = len(treatments) / len(df)
                         goodys_ratios.append(goodys_ratio)
                         faultys_rations.append(faulty_ratio)
                         ratios[file_name] = {"goody" : goodys_ratio , "faulty" : faulty_ratio }
               except Exception as e:
                    logger.error(f"could not find the the ratio for file : {file_name}")
          
          try:
               with open(f"./internal/oxn/transformed/ratios.json", "w") as json_file:
                    json.dump(ratios, json_file)

               logger.info("wrote data to disk")
          except Exception as e:
               logger.error(str(e))
          logger.info(f"average ratio of goody traces : {sum(goodys_ratios) / len(goodys_ratios)}")
          logger.info(f"average ration of faulty traces : {sum(faultys_rations) / len(faultys_rations)}")
          

     def get_error_entire_code_ratio(self):
          train_path = "./internal/oxn/transformed"
          files_list = os.listdir(train_path)
          prob_rations = {}

          no_treatment_error_sum = 0
          no_treatment_no_error_sum = 0

          treatment_error_sum = 0
          treatment_no_error_sum = 0

          for file in files_list:
               if file == "ratios.json" or file == "entire_error_ratios.json":
                    continue

                    
               df = pd.read_csv(f"{train_path}/{file}")
               delay_treatment_df = df[df["delay_treatment"] == "delay_treatment"]
               no_treatment_df = df[df["delay_treatment"] == "NoTreatment"]

               no_treatment_df["has_error_in_trace"] = no_treatment_df["has_error_in_trace"].astype(float)
               no_treatment_error = no_treatment_df[no_treatment_df["has_error_in_trace"] == 1.0]
               no_treatment_no_error = no_treatment_df[no_treatment_df["has_error_in_trace"] == 0.0] 

               delay_treatment_df["has_error_in_trace"] = delay_treatment_df["has_error_in_trace"].astype(float)
               treatment_error = delay_treatment_df[delay_treatment_df["has_error_in_trace"] == 1.0]
               treatment_no_error = delay_treatment_df[delay_treatment_df["has_error_in_trace"] == 0.0]
               """
               prob_rations[file] = {
                    "no_treatment_error" : len(no_treatment_error) / len(no_treatment_df),
                    "no_treatment_no_error" : len(no_treatment_no_error) / len(no_treatment_no_error),
                    "treatment_error" : len(treatment_error) / len(delay_treatment_df),
                    "treatment_no_error" : len(treatment_no_error) / len(delay_treatment_df) 
               }
               """
               no_treatment_error_sum += (len(no_treatment_error) / len(no_treatment_df))
               no_treatment_no_error_sum += (len(no_treatment_no_error) / len(no_treatment_df))
               treatment_error_sum += (len(treatment_error) / len(delay_treatment_df))
               treatment_no_error_sum += (len(treatment_no_error) / len(delay_treatment_df))

          
          entire_error_ratios = {
               "no_treatment_error" : no_treatment_error_sum / len(files_list),
               "no_treatment_no_error": no_treatment_no_error_sum / len(files_list),
               "treatment_error": treatment_error_sum / len(files_list),
               "treatment_no_error": treatment_no_error_sum / len(files_list)
          }

          with open(f"./internal/oxn/transformed/entire_error_ratios.json", "w") as json_file:
                    json.dump(entire_error_ratios, json_file)

          logger.info("wrote data to disk")





     def train_model(self):
          train_path = "./internal/oxn/transformed"
          files_list = os.listdir(train_path)

          trace_response_variables : list[pd.DataFrame] = []

          for file in files_list:
               if "config" in file:
                    continue
               if "entire" in file: 
                    continue
               if "ratios" in file:
                    continue

               trace_response_variables.append(pd.read_csv(f"{train_path}/{file}"))
          
          dataset = pd.concat(trace_response_variables, ignore_index=True)
          one_hot_encoding_col_names = gen_one_hot_encoding_col_names()
          col_names_for_input_data = build_colum_names_for_adf_mat_df()
          col_names_for_input_data.append("has_error_in_trace")
          torch_dataset = TraceVariableDatasetInference(dataframe=dataset, labels=one_hot_encoding_col_names, input_names=col_names_for_input_data)
          train_size = int(0.8 * len(torch_dataset)) 
          test_size = len(torch_dataset) - train_size
          training_data, test_data = random_split(torch_dataset, [train_size, test_size])

          train_dataloader = DataLoader(training_data, batch_size=100, shuffle=True)
          test_dataloader = DataLoader(test_data, batch_size=100, shuffle=True)

          precision_per_batch_recom, precision_per_batch_no_fault, other_class_ratios_training  = self.trace_model.train_trace_model(train_loader=train_dataloader, num_epochs=3)
          self.trace_model.save_model_dict(constants.MODEL_PATH)
          precison_recom, precison_no_fault, ratio_other_class_predictions_test = self.trace_model.test_trace_model(test_loader=test_dataloader)

          average_test_precison_recom = sum(precison_recom) / len(precison_recom)
          average_test_precision_no_fault = sum(precison_no_fault) / len(precison_no_fault)

          #logger.info(f"The average precision in recom class : {sum(precison_recom) / len(precison_recom)}")
          #logger.info(f"The overall precision in the no fault class : {sum(precison_no_fault) / len(precison_no_fault)}")
 
          visualize_training_precision( precision_per_batch_recom, precision_per_batch_no_fault, other_prediction_ratio=other_class_ratios_training, training_or_test="Training" , filename="1_hidden_layer_training_with_ratios_3_3_epochs.png")
          visualize_training_precision( precison_recom, precison_no_fault, other_prediction_ratio=ratio_other_class_predictions_test, training_or_test="Test" , filename="1_hidden_layer_test_with_ratios_3_3_epochs.png")
          plot_average_precisions(average_test_precison_recom, average_test_precision_no_fault, "1_hidden_layer_average_results_3_3_epochs.png")
          
     



          




               





          





     
     


     

          
     

          