"""
This class acts as a Boundary Class for the fastAPI.
"""


from RWDGController import RWDGController
from TraceResponseVariable import TraceResponseVariable
from StorageClient import LocalStorageHandler
from TraceModel import TraceModel
from exceptions import OXNFileNotFound, NoDataForExperiment
from ModelController import ModelController


class AnalysisManager:

     def __init__(self, experiment_id : str, local_storage_handler : LocalStorageHandler , trace_model : TraceModel) -> None:
          self.storage_handler : LocalStorageHandler = local_storage_handler
          self.experiment_id : str = experiment_id
          self.response_variables : list[TraceResponseVariable] = self._get_data_for_variables()
          self.experiment_label : str = self._get_label_for_experiment()
          self.rwdg_controller = RWDGController(self.response_variables, self.experiment_id, self.experiment_label)
          self.model_controller = ModelController(self.response_variables, self.experiment_id, model=trace_model, experiment_label=self.experiment_label, local_storage_handler=local_storage_handler)
     
     def _get_data_for_variables(self) -> list[TraceResponseVariable]:
          files_list = self.storage_handler.list_files_in_dir(self.experiment_id)
          if len(files_list) == 0:
               raise OXNFileNotFound(f"Cannot find data for experiment with ID: {self.experiment_id}")

          response_variables : list[TraceResponseVariable] = []

          for file in files_list:
               if "config" in file:
                    continue
               tup = self.storage_handler.get_file_from_dir(file)
               if tup is None:
                    print(f"Could not retrieve data for file: {file}")
                    continue
               response_variables.append(TraceResponseVariable(tup[0],self.experiment_id, tup[1] ))
          
          if len(response_variables) == 0:
               raise NoDataForExperiment(f"Could not retrieve any Data for experiment with ID: {self.experiment_id}")
          
          return response_variables
     
     def _get_label_for_experiment(self) -> str:
          return self.storage_handler.get_experiment_label(self.experiment_id)
     
     def analyze_experimment(self) -> tuple[dict[str, list[dict[str, float]]], dict[str, list[dict[str, float]]]]:
          self.rwdg_controller.iterate_over_varibales()
          return self.model_controller.evaluate_variables()
       



