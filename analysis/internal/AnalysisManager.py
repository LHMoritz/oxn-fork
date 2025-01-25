"""
This class acts as a Boundary Class for the fastAPI.
"""


from analysis.internal.RWDGController import RWDGController
from analysis.internal.TraceResponseVariable import TraceResponseVariable
from analysis.internal.StorageClient import LocalStorageHandler
from analysis.internal.TraceModel import TraceModel
from analysis.internal.exceptions import OXNFileNotFound, NoDataForExperiment, ConfigFileNotFound, LabelNotPresent, BatchExperimentsNotSupported
from analysis.internal.ModelController import ModelController
import logging
import time


logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    FileNotFoundError: "Error Accessing the Database: {}",
    OXNFileNotFound: "Could not find experiment in the Database: {}",
    NoDataForExperiment: "No Data present for experiment: {}",
    ConfigFileNotFound: "Could not find Configuration for experiment: {}",
    LabelNotPresent: "Could not find label for supervised learning in config file: {}",
}

def batch_predicate(file_name : str) -> bool:
     return "batch" in file_name


class AnalysisManager:

     def __init__(self, experiment_id : str, local_storage_handler : LocalStorageHandler , trace_model : TraceModel) -> None:
          self.storage_handler : LocalStorageHandler = local_storage_handler
          self.experiment_id : str = experiment_id
          self.failed_files : list[str] = []
          self.time_to_result : float = -1.0
          self.response_variables : list[TraceResponseVariable] = self._get_data_for_variables()
          self.experiment_label : str = self._get_label_for_experiment()
          self.rwdg_controller = RWDGController(self.response_variables, self.experiment_id, self.experiment_label)
          self.model_controller = ModelController(self.response_variables, self.experiment_id, model=trace_model, experiment_label=self.experiment_label, local_storage_handler=local_storage_handler)

     
     def _get_data_for_variables(self) -> list[TraceResponseVariable]:
          files_list = self.storage_handler.list_files_in_dir(self.experiment_id)
          if len(files_list) == 0 :
               logger.error(f"Could not find any data for ex: {self.experiment_id}")
               raise OXNFileNotFound(f"Cannot find data for experiment with ID: {self.experiment_id}")
          
          batch_files = list(filter(batch_predicate, files_list ))
          if len(batch_files) > 0:
               logger.error("Batch Experiments not yet supported")
               raise BatchExperimentsNotSupported("Batch Experiments not yet supported")

          response_variables : list[TraceResponseVariable] = []

          for file in files_list:
               if "config" in file:
                    continue
               # checking for metric data
               if "trace" not in file:
                    logging.debug(f"file with name: {file} not a trace variable")
                    continue
               tup = self.storage_handler.get_file_from_dir(file)
               if tup is None:
                    logger.info(f"Could not retrieve data for file: {file}")
                    self.failed_files.append(file)
                    continue
               response_variables.append(TraceResponseVariable(tup[0],self.experiment_id, tup[1] ))
          
          if len(response_variables) == 0:
               logger.error(f"Could not retrieve any Data for experiment with ID: {self.experiment_id}")
               raise NoDataForExperiment(f"Could not retrieve any Data for experiment with ID: {self.experiment_id}")
          
          logger.info(f"instantiated {len(response_variables)} Trace ResponseVarables.")
          return response_variables
     
     def _get_label_for_experiment(self) -> str:
          return self.storage_handler.get_experiment_label(self.experiment_id)
     
     def analyze_experiment(self) -> tuple[dict[str, list[dict[str, float]]], dict[str, list[dict[str, float]]]]:
          logging.info(f"starting analysis")
          start_time = time.time()
          self.rwdg_controller.iterate_over_varibales()
          tup = self.model_controller.evaluate_variables()
          end_time = time.time()
          self.time_to_result = end_time - start_time
          
          result = {
               "experiment_id" : self.experiment_id,
               "metrics" : tup[0] if  tup is not None else [],
               "probability" : tup[1] if tup is not None else [],
               "failedVariables" : str(self.failed_files),
               "timeToResult" : self.time_to_result
          }
          self.storage_handler.write_json_to_directory(f"{self.experiment_id}_analysis_results", result)
     """
     def _construct_message(self, e: Exception | None) -> str:
          if e is None:
               return "Ok"
          for exception_type, message in ERROR_MESSAGES.items():

               if isinstance(e, exception_type):
                    return message.format(str(e))
               
          return f"An error occurred: {str(e)}"
     """