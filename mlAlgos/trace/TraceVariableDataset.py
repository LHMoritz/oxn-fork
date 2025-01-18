
import pandas as pd
from torch.utils.data import Dataset
import torch

'''
This class can be seen as putting a single variable through the model.
It will create 
'''

class TraceVariableDataset(Dataset):
    def __init__(self, dataframe: pd.DataFrame, labels: list[str], input_names: list[str]):
        self.dataframe: pd.DataFrame = dataframe
        self.col_names_labels: list[str] = labels
        self.col_names_input: list[str] = input_names
        

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, index) -> tuple[torch.tensor, torch.tensor]:
        # Extract the row as a pandas Series
        row_series: pd.Series = self.dataframe.iloc[index]

        # Process labels
        labels_list = row_series[self.col_names_labels]
        labels_list_as_list = labels_list.astype(float).to_list()
        labels_tensor = torch.Tensor(labels_list_as_list)
        print(labels_tensor)
        print(labels_tensor.shape)

        # Process inputs
        input_cols_list = row_series[self.col_names_input].astype(float).to_list()
        input_tensor = torch.Tensor(input_cols_list)

        return input_tensor, labels_tensor



