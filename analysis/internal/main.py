
from StorageClient import LocalStorageHandler
from RWDGController import RWDGController
from TraceResponseVariable import TraceResponseVariable
import pandas as pd
from torch.utils.data import DataLoader, random_split
from TraceModel import TraceModel, vizualize_training_err_and_acc
import torch.nn as nn
import matplotlib.pyplot as plt
import internal.constants as constants
from analysis.internal.TraceVariableDatasetInference import TraceVariableDatasetInference
from ModelController import ModelController
import torch
from utils import load_model


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



"""
if __name__=='__main__':
     test_inference()
"""












