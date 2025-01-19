
from StorageClient import LocalStorageHandler
from RWDGController import RWDGController
from TraceResponseVariable import TraceResponseVariable
import pandas as pd
from torch.utils.data import DataLoader, random_split
from TraceModel import TraceModel, vizualize_training_err_and_acc
import torch.nn as nn
import matplotlib.pyplot as plt
import constants
from TraceVariableDataset import TraceVariableDataset
from ModelController import ModelController
import torch


def main():

     print(torch.tensor([1,2,3]))

     storage_handler = LocalStorageHandler("data")
     file_list = storage_handler.list_files_in_dir("experiment_data")
     
     response_variables = []
     for file in file_list:
          res_data = storage_handler.get_file_from_dir("experiment_data", file)
          response_variables.append(TraceResponseVariable(res_data, "experiment_data", file))
     
     con= RWDGController(response_variables, "experiment_data",  "recommendationservice")
     con.iterate_over_varibales()

     #for var in con.variables:
     #     print(var.adf_matrices.head())
     #     print(var.error_ratio)

     # adding some machine learning
     dataset = pd.concat([var.adf_matrices for var in con.variables], ignore_index=True)
     one_hot_encoding_col_names = con.one_hot_encoding_column_names
     col_names_for_input_data = con.column_names
     torch_dataset = TraceVariableDataset(dataframe=dataset, labels=one_hot_encoding_col_names, input_names=col_names_for_input_data)
     train_size = int(0.8 * len(torch_dataset)) 
     test_size = len(torch_dataset) - train_size
     training_data, test_data = random_split(torch_dataset, [train_size, test_size])

     train_dataloader = DataLoader(training_data, batch_size=100, shuffle=False)
     test_dataloader = DataLoader(test_data, batch_size=100, shuffle=False)

     # dim = 1 is important because the logit (tensor) of the network has the shape (batch_sie, number of classes)
     my_trace_model = TraceModel(nn.CrossEntropyLoss(), [225, 1500, 1500, 1500, 15],  nn.ReLU())

     errors, acc = my_trace_model.train_trace_model(train_loader=train_dataloader, iterations=1000)

     my_trace_model.save_model_dict(constants.MODEL_PATH)
     vizualize_training_err_and_acc(err=errors, acc=acc)

     
#main()

def init_model():
     my_trace_model = TraceModel(nn.CrossEntropyLoss(), [225, 1500, 1500, 1500, 15],  nn.ReLU())

#init_model()

def test_inference():
     storage_handler = LocalStorageHandler("data")
     file_list = storage_handler.list_files_in_dir("experiment_data")
     
     response_variables = []
     for file in file_list:
          res_data = storage_handler.get_file_from_dir("experiment_data", file)
          response_variables.append(TraceResponseVariable(res_data, "experiment_data", file))
     
     con= RWDGController(response_variables, "experiment_data",  "recommendationservice")
     con.iterate_over_varibales()

     evaluater = ModelController(response_variables, "experiment_data",constants.MODEL_PATH, 12 , local_storage_handler=storage_handler)

     evaluater.model.parameters

     evaluater.evaluate_variables()

     evaluater._save_cond_prob_to_disk()
     evaluater._save_metrics_to_disk()

#test_inference()

def test_model_controller():
     storage_handler = LocalStorageHandler("data")
     file_list = storage_handler.list_files_in_dir("experiment_data")
     
     response_variables = []
     for file in file_list:
          res_data = storage_handler.get_file_from_dir("experiment_data", file)
          response_variables.append(TraceResponseVariable(res_data, "experiment_data", file))
     m = ModelController(response_variables, "experiment_data",constants.MODEL_PATH, 12 , local_storage_handler=storage_handler)

#test_model_controller()

def test():

     a = torch.tensor([1,2,3,4],dtype=torch.float32)
     print(a)
     print(type(a))
 
#test()

def soemthing():
     evaluater = ModelController(None , "experiment_data",constants.MODEL_PATH, 12 , local_storage_handler=None)

     for param in evaluater.model.parameters():
          print(param.shape)

#soemthing()

if __name__=='__main__':
     #main()
     test()
     test_inference()













