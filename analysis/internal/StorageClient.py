
from __future__ import annotations
from abc import ABC, abstractmethod
import os
import constants
import pandas as pd
from pathlib import Path
import json
from exceptions import OXNFileNotFound, BatchExperimentsNotSupported, LabelNotPresent, ConfigFileNotFound
from utils import get_treatment_column
import numpy as np

class StorageHandler(ABC):

     @abstractmethod
     def list_files_in_dir(self, dir_name) -> list[str]:
          '''
          This class lists all Filenames in a directory
          '''
     
     @abstractmethod
     def write_json_to_directory(self, dir_name, file_name, file_content) -> None:
          '''
          writes File to directory given the name and the content
        '''
     @abstractmethod
     def get_file_from_dir(self, file_path):
          '''
          retrieves file from directory
          '''
     
# TODO add rel_path offset in all functions

def config_predicate(name:str) -> bool:
     return "config" in name

class LocalStorageHandler(StorageHandler):

     def __init__(self, base_path :str) -> None:
          super().__init__()
          self.experiment_path = Path(base_path) / 'experiments'
     
     """
     Gets the label for the experiment (the Microservice name in which the fault was injected)
     """
     def get_experiment_label(self, experiment_id : str) -> str:
          files = self.list_files_in_dir(experiment_id=experiment_id)
          num = list(filter(config_predicate, files))
          if len(num) > 1:
               raise BatchExperimentsNotSupported("Batch Experiments not yet supported for Deep Learning")
          elif len(num) == 0:
               raise ConfigFileNotFound(f"Could not find experiement configuration file for  experiment: {experiment_id}")

          with open(Path(self.experiment_path) / num[0], "r") as file:
               data = json.load(file)
          labels = []
          for treatment in data["spec"]["experiment"]["treatments"]:
               params = treatment.get("add_security_context", treatment.get("loss_treatment", {})).get("params", {})
               if "label" in params:
                    labels.append(params["label"])
          
          if len(labels) >= 1:
               return labels[0]
          else:
               raise LabelNotPresent(f"Label for supervised learning not found")
     
     def list_files_in_dir(self, experiment_id :str) -> list[str]:
          try:
               files = os.listdir(self.experiment_path)
               return  list(filter(lambda x : experiment_id in x , files))
          except FileNotFoundError:
               print("err")
               return []
     
     """
     def write_file_to_directory(self, dir_name, file_name, file_content: pd.DataFrame) -> None:
          try:
               os.makedirs(dir_name, exist_ok=True)
               file_path = os.path.join(dir_name, file_name)
               file_content.to_csv(file_path, index=False)
          except Exception as e:
               print(f"Error: Could not write file '{file_name}' to '{dir_name}'. {e}")
     
     """

     def write_json_to_directory(self, file_name : str, file_content : dict) -> None:
          try:
               file_path = os.path.join(self.experiment_path, f"{file_name}.json")
               with open(file_path, "w") as json_file:
                    json.dump(file_content, json_file)
          except IOError as e:
               pass

     
     def get_file_from_dir(self, file_name:str) -> tuple[pd.DataFrame, str] | None:
          try:
               file_path = Path(self.experiment_path) / file_name
               print(file_path)
               with open(file_path, 'r' ) as file:
                    data = json.load(file)
               df =  pd.DataFrame(data)
               df.replace(['N/A', 'null', ''], np.nan, inplace=True)

               if not self.check_columns_exist(df, constants.REQUIRED_COLUMNS) :
                    return None

               service_name = df.iloc[0]["service_name"]
               return df, service_name
          except FileNotFoundError:
               print(f"Error: File for : {file_name} not found")
               return None
          except pd.errors.EmptyDataError:
               print(f"Error: File {file_name} is empty or has invalid data.")
               return None
          except Exception as e:
               print(f"Could not retrieve {e} ")
               return None
     
     def check_columns_exist(self, data : pd.DataFrame, required_columns : list[str] ) -> bool:
          missing_columns = [col for col in required_columns if col not in data.columns]
          treatment = get_treatment_column(list(data.columns))
          return len(missing_columns) == 0 and treatment != ""

"""
if __name__=='__main__':
     handler = LocalStorageHandler("oxn")
     print(handler.list_files_in_dir("01737208087"))
     print(handler.list_files_in_dir("01737287"))
     a = {"x" : "y"}
     handler.write_json_to_directory("analysis", a)

     print(handler.get_experiment_label("01737208087"))
     tup = handler.get_file_from_dir('01737208087_frontend_traces.json')
     if tup is not None:
          print(tup[0].head(5))
          print(tup[1])
     
"""




