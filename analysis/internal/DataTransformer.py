

from analysis.internal.StorageClient import LocalStorageHandler
from analysis.internal.RWDGController import RWDGController
from analysis.internal.TraceResponseVariable import TraceResponseVariable
from analysis.internal.TraceModel import TraceModel, vizualize_test_err_and_acc, vizualize_training_err_and_acc
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


"""
     This class is forn transforming data on disk. To actually train  the Multilayer-Perceptron.
"""
class DataTransformerAndAnalyzer():

     def __init__(self, storage_handler : LocalStorageHandler):
          self.storage_handler = storage_handler
          self.trace_model = TraceModel(nn.CrossEntropyLoss(), constants.MODEL_DIMENSIONS,  nn.ReLU())
     
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
     
     def train_model(self):
          train_path = "./internal/oxn/transformed"
          files_list = os.listdir(train_path)

          trace_response_variables : list[pd.DataFrame] = []

          for file in files_list:
               if "config" in file:
                    continue

               trace_response_variables.append(pd.read_csv(f"{train_path}/{file}"))
          

          dataset = pd.concat(trace_response_variables, ignore_index=True)
          one_hot_encoding_col_names = gen_one_hot_encoding_col_names()
          col_names_for_input_data = build_colum_names_for_adf_mat_df()
          torch_dataset = TraceVariableDatasetInference(dataframe=dataset, labels=one_hot_encoding_col_names, input_names=col_names_for_input_data)
          train_size = int(0.8 * len(torch_dataset)) 
          test_size = len(torch_dataset) - train_size
          training_data, test_data = random_split(torch_dataset, [train_size, test_size])

          train_dataloader = DataLoader(training_data, batch_size=100, shuffle=False)
          test_dataloader = DataLoader(test_data, batch_size=1, shuffle=False)

          train_err, train_acc = self.trace_model.train_trace_model(train_loader=train_dataloader, iterations=1000)
          self.trace_model.save_model_dict(constants.MODEL_PATH)
          test_err, test_acc = self.trace_model.test_trace_model(test_loader=test_dataloader )
 

          vizualize_training_err_and_acc(train_err, train_acc)
          vizualize_test_err_and_acc(test_err, test_acc)

          




               





          





     
     


     

          
     

          