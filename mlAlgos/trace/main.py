
from StorageClient import LocalStorageHandler
from RWDGController import RWDGController
from TraceResponseVariable import TraceResponseVariable
import pandas as pd
from torch.utils.data import DataLoader, random_split
from TrainAndTestModel import train_trace_model, TraceModel, NumpyDataset, save_model_dict
import torch.nn as nn
import matplotlib.pyplot as plt
import constants


def main():

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
     torch_dataset = NumpyDataset(dataframe=dataset)
     train_size = int(0.8 * len(torch_dataset)) 
     test_size = len(torch_dataset) - train_size
     training_data, test_data = random_split(torch_dataset, [train_size, test_size])

     train_dataloader = DataLoader(training_data, batch_size=100, shuffle=False)
     test_dataloader = DataLoader(test_data, batch_size=100, shuffle=False)

     my_trace_model = TraceModel(nn.CrossEntropyLoss(), [196, 1500, 1500, 1500, 14], [nn.ReLU(), nn.ReLU(), nn.ReLU(), nn.Softmax()])

     errors, acc = train_trace_model(trace_model=my_trace_model, train_loader=train_dataloader, iterations=5000)

     save_model_dict(my_trace_model, constants.MODEL_PATH)
     print(errors)
     print(acc)
     
main()










