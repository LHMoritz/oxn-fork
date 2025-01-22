
from numpy import dtype, float32
import pandas as pd
from torch.utils.data import Dataset
import torch

'''
This class can be seen as putting a single variable through the model.
It will create the input for the Model
'''

class TraceVariableDatasetInference(Dataset):
    def __init__(self, dataframe: pd.DataFrame, labels: list[str], input_names: list[str]):
        self.dataframe: pd.DataFrame = dataframe
        self.col_names_labels: list[str] = labels
        self.col_names_input: list[str] = input_names
        

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, index) -> tuple[torch.Tensor, torch.Tensor]:

        row_series: pd.Series = self.dataframe.iloc[index]

        # Process labels
        labels_list = row_series[self.col_names_labels]
        labels_list_as_list = labels_list.astype(float).to_list()
        labels_tensor = torch.tensor(labels_list_as_list, dtype=torch.float32)
        #print(labels_tensor)
        #print(labels_tensor.shape)

        # Process inputs
        input_cols_list = row_series[self.col_names_input].astype(float).to_list()
        input_tensor = torch.tensor(input_cols_list, dtype=torch.float32)

        return input_tensor, labels_tensor



