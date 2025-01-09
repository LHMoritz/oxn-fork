
import pandas as pd
from torch.utils.data import Dataset
import torch

'''
This class can be seen as putting a single variable through the model.
It will create 
'''
class TraceVariableDataset(Dataset):
     
     def __init__(self, dataframe : pd.DataFrame, labels : list[str], input_names : list[str]):
          self.dataframe : pd.DataFrame = dataframe
          self.col_names_labels : list[str] = labels
          self.col_names_input : list[str] = input_names

     def __len__(self):
          return len(self.dataframe)

     '''
     Here we have to give back the input and the actual label of the this dataframe row (trace we have coverted in the row).
     We have to convert it to tensors so we can use it with our model.
     '''
     def __getitem__(self, index):
          # gives back a pandas series
          row_series : pd.Series = self.dataframe.iloc[index]

          # getting the labels in one-hot-encoding fashion
          labels_list = row_series[self.col_names_labels]
          labels_list = labels_list.astype(float)
          labels_tensor = torch.tensor(labels_list.values, dtype=torch.float32)

          # getting the corresponding input tensor
          input_cols_list = row_series[self.col_names_input]
          input_cols_list = input_cols_list.astype(float)
          input_tensor = torch.tensor(input_cols_list.values, dtype=torch.float32)
          # supervised learning, give back the input and the target as a tuple
          return input_tensor, labels_tensor


