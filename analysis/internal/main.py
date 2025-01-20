
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
from utils import load_model



def build_new_model():
     handler = LocalStorageHandler("oxn")
     files_list = handler.list_files_in_dir("01737208087")
     if len(files_list) == 0:
         print("What?")

     response_variables : list[TraceResponseVariable] = []

     for file in files_list:
          if "config" in file:
               continue
          tup = handler.get_file_from_dir(file)
          if tup is None:
               print("Why non")
               exit()
          response_variables.append(TraceResponseVariable(tup[0],"01737208087", tup[1] ))
     
     ex_label = handler.get_experiment_label("01737208087")
     
     con = RWDGController(response_variables, "01737208087",ex_label )
     
     con.iterate_over_varibales()

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
     # here check the in and out dimentsion!
     my_trace_model = TraceModel(nn.CrossEntropyLoss(), [256, 1500, 1500, 1500, 17],  nn.ReLU())

     errors, acc = my_trace_model.train_trace_model(train_loader=train_dataloader, iterations=1000)

     my_trace_model.save_model_dict(constants.MODEL_PATH)
     vizualize_training_err_and_acc(err=errors, acc=acc)


def test_inference():
     handler = LocalStorageHandler("oxn")
     files_list = handler.list_files_in_dir("01737208087")
     if len(files_list) == 0:
         print("What?")

     response_variables : list[TraceResponseVariable] = []

     for file in files_list:
          if "config" in file:
               continue
          tup = handler.get_file_from_dir(file)
          if tup is None:
               print("Why non")
               exit()
          response_variables.append(TraceResponseVariable(tup[0],"01737208087", tup[1] ))
     
     ex_label = handler.get_experiment_label("01737208087")
     
     con = RWDGController(response_variables, "01737208087",ex_label )
     
     con.iterate_over_varibales()

     model = load_model()
     mod_con = ModelController(response_variables,"01737208087", model, ex_label, handler)
     mod_con.evaluate_variables()




if __name__=='__main__':
     #main()
     #test()
     #test_inference()
     #test_model_controller2()
     #build_new_model()
     test_inference()













