
from StorageClient import LocalStorageHandler
from RWDGController import RWDGController
from TraceResponseVariable import TraceResponseVariable
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

     for var in con.variables:
          print(var.adf_matrices.head())
          print(var.error_ratio)
     
main()










