
from __future__ import annotations
from abc import ABC, abstractmethod
import os
import internal.constants as constants
import pandas as pd
from pathlib import Path
import json
from internal.exceptions import  BatchExperimentsNotSupported, LabelNotPresent, ConfigFileNotFound
from internal.utils import get_treatment_column
import numpy as np
import logging
import re

logger = logging.getLogger(__name__)

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
     


def config_predicate(name:str) -> bool:
     return "config" in name

class LocalStorageHandler(StorageHandler):

     def __init__(self, base_path :str) -> None:
          super().__init__()
          self.experiment_path = Path(base_path) / 'experiments'
          self.analysis_path = Path(base_path) / 'analysis'
     
     """
     Gets the label for the experiment (the Microservice name in which the fault was injected)
     """
     def get_experiment_label(self, experiment_id : str) -> str:
          files = self.list_files_in_dir(experiment_id=experiment_id)
          logger.debug(files)
          num = list(filter(config_predicate, files))
          if len(num) > 1:
               logger.error(f"Several config files found for id: {experiment_id}")
               raise BatchExperimentsNotSupported("Batch Experiments not yet supported for Deep Learning")
          elif len(num) == 0:
               logger.error(f"no config file present for experiment wiht ID : {experiment_id}")
               raise ConfigFileNotFound(f"Could not find experiement configuration file for  experiment: {experiment_id}")

          with open(Path(self.experiment_path) / num[0], "r") as file:
               data = json.load(file)

          try:
               add_security_context = data['spec']['experiment']['treatments'][0]['add_security_context']
               if "label" not in add_security_context['params']:
                    logger.error("Label for supervised learning not found")
                    raise LabelNotPresent("Label for supervised learning not found")
               a = add_security_context['params']['label']
               logger.info(a)
               return  a
          except KeyError as e:
               logger.error(f"could not find label for supervised Learning: {e}")
               raise LabelNotPresent("Label for supervised learning not found")

     
     def list_files_in_dir(self, experiment_id :str) -> list[str]:
          try:
               files = os.listdir(self.experiment_path)
               file_names =  list(filter(lambda x : experiment_id in x , files))
               logger.debug(f"found files for id : {experiment_id} : {str(file_names)}")
               return file_names
          except FileNotFoundError:
               logging.error(f"no files in DB for experiment_id: {experiment_id}")
               return []
     

     def write_json_to_directory(self, file_name : str, file_content : dict) -> None:
          try:
               file_path = os.path.join(self.analysis_path, f"{file_name}.json")
               with open(file_path, "w") as json_file:
                    json.dump(file_content, json_file)
               
               logger.info("wrote results to the analysis datastore")
          except IOError as e:
               logger.error("could not write results to the analysis datastore")

     
     def get_file_from_dir(self, file_name:str) -> tuple[pd.DataFrame, str] | None:
          try:
               file_path = Path(self.experiment_path) / file_name
               with open(file_path, 'r' ) as file:
                    data = json.load(file)
               df =  pd.DataFrame(data)
               df.replace(['N/A', 'null', ''], np.nan, inplace=True)

               if not self._check_columns_exist(df, constants.REQUIRED_COLUMNS) :
                    return None

               service_name = self._retrieve_service_name(file_name)
               logging.debug(f"this is the service name {service_name}")
               return df, service_name
          except FileNotFoundError:
               logger.info(f"Error: File for : {file_name} not found")
               return None
          except pd.errors.EmptyDataError:
               logger.info(f"Error: File {file_name} is empty or has invalid data.")
               return None
          except Exception as e:
               logger.info(f"Could not retrieve {e} ")
               return None
     
     def _check_columns_exist(self, data : pd.DataFrame, required_columns : list[str] ) -> bool:
          missing_columns = [col for col in required_columns if col not in data.columns]
          treatment = get_treatment_column(list(data.columns))
          return len(missing_columns) == 0 and treatment != ""

     def _retrieve_service_name(self, file_name : str) -> str:
          pattern = r'_(.*?)_traces\.json'
          match = re.search(pattern, file_name)
          if match:
               return match.group(1)
          else:
               return file_name


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




