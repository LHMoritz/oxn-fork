
from urllib import response
from analysis.internal.TraceResponseVariable import TraceResponseVariable
import pandas as pd
import analysis.internal.constants as constants
import numpy as np
from analysis.internal.utils import gen_one_hot_encoding_col_names, build_colum_names_for_adf_mat_df, get_treatment_column, get_index_for_service_label
from analysis.internal.exceptions import ColumnsNotPresent
import logging

'''
This class Takes in  a dataframe from with distributed tracing data and generates a dataframe
with 'adjency matrices' for each trace that captures the average response times between services.
It is part of the RWDG Trace model and therefore part for the data wranglin for the Multilayer perceptron.
'''
# TODO : add internal spans to the next parent there , test

# TODO : interesting KPI: how many faulty traces do have error fields in there, how many "good traces have error fields"

# TODO : how much do the distribution differ from each other between fault and no fault for each response variable?
# we still have the assumtion for a 

logger = logging.getLogger(__name__)

def mean_normalization( val : float, mean: float, min: float , max : float) -> float:
     nominator = val - mean
     denominator = max - min
     if denominator > 0:
          return nominator / denominator
     else:
          return 0.0

class RWDGController:

     def __init__(self, variables : list[TraceResponseVariable], experiment_id,  injected_service: str):
          self.variables : list[TraceResponseVariable] = variables
          self.experiment_id : str = experiment_id
          #self.weights_of_edges : dict[str, float] = None
          self.service_name_mapping : dict[str , int] = constants.SERVICES # TODO change later to call a route on that
          self.service_name_mapping_backward = constants.SERVICES_REVERSE
          self.column_names = build_colum_names_for_adf_mat_df()
          self.injected_service = get_index_for_service_label(injected_service)
          self.one_hot_encoding_for_exp : list[float] = self.gen_one_hot_encoding_for_exp()
          if len(self.one_hot_encoding_for_exp) == 0:
               raise ColumnsNotPresent("Not all needed columns in the Dataframe are present")
          self.one_hot_encoding_column_names = gen_one_hot_encoding_col_names()
          self.supervised_column = get_treatment_column(list(self.variables[0].data.columns))

     '''Normalizes the calculated weight matrices after the mean normalization
          This has the affect that each value is in range [0, 1] '''
     def normalizes_response_variables(self):

          # we do not want to do it with error_code columns, just the 
          numerical_column_names = self.column_names[:len(self.column_names) -1]

          for var in self.variables:
               if var.adf_matrices	is not None:
                    avg_values = []
                    max_values = []
                    min_values = []
                    for col in numerical_column_names:
                         avg_values.append(var.adf_matrices[col].mean())
                         max_values.append(var.adf_matrices[col].max())
                         min_values.append(var.adf_matrices[col].min())

                    for idx in range(len(numerical_column_names)):
                         var.adf_matrices[self.column_names[idx]].apply(mean_normalization, args=(avg_values[idx], min_values[idx], max_values[idx]))
          

     '''
     This functions labels the trace with a boolean column:
     1 : if at least one span has an error field (http or Grpc)
     0 : if there is no error
     '''
     def trace_has_error(self, trace_data : pd.DataFrame) -> int:
          has_error = 0
          for _ , val in trace_data[constants.REQ_STATUS_CODE].items():
               if pd.isna(val):
                    continue
               val = str(int(val))
               if len(val) == 3:
                    # http status code
                    if self.is_http_error(val):
                         has_error = 1
                         return has_error
               
               elif len(val) <= 2:
                    # gRPC status code
                    if self.is_grpc_error(val):
                         has_error = 1
                         return has_error
          
          return has_error
     
     def is_http_error(self, http_status_code : str) -> bool:
          return (http_status_code[0] == "4" or http_status_code[0] == "5")

     def is_grpc_error(self, grpc_status_code : str) -> bool:
          return not grpc_status_code == "0"

                    
     '''
     This functions iterates over all the trace responsevariables and does the data transformation and the
     KPI calculation for each variable
     '''
     def iterate_over_varibales(self)-> None:
          for var in self.variables:
               self._adj_mat_for_var(var)
               self._calc_error_ratio_for_var(var)
          
          self.normalizes_response_variables()
     
     def _adj_mat_for_var(self , response_variable : TraceResponseVariable)-> None:
          dataframe_rows = []
          group_df = response_variable.data.groupby(constants.TRACE_ID_COLUMN)
          for _, single_trace_data in group_df:
               new_row = []
               raw_adj = self.gen_adf(single_trace_df=single_trace_data)
               weighted = self._weight_adjency_matrix(raw_adj)
               new_row.append(single_trace_data[constants.TRACE_ID_COLUMN].iloc[0])
               new_row.extend(np.array(weighted).flatten())
               new_row.append(response_variable.service_name)
               new_row.append(self.trace_has_error(single_trace_data))
               new_row.extend(self.one_hot_encoding_for_exp)
               new_row.append(single_trace_data[self.supervised_column].iloc[0])
               dataframe_rows.append(new_row)
          
          # unpack the colum names
          '''Microservice name is here important. Later on we are going to merge the dataframes for each response variable and we still wan to have a direct mapping towards a service '''
          '''[trace_id, flattened_out weighted adj matrix, microservice_name, one hot encoding for treatment]'''
          #print(dataframe_rows[0])
         # print("_________________")
          #print([constants.TRACE_ID_COLUMN, *self.column_names, "microservice_name", constants.ERROR_IN_TRACE_COLUMN, *self.one_hot_encoding_column_names, self.supervised_column])
         # exit(1)
          response_variable.adf_matrices = pd.DataFrame(dataframe_rows , columns=[constants.TRACE_ID_COLUMN, *self.column_names, "microservice_name", constants.ERROR_IN_TRACE_COLUMN, *self.one_hot_encoding_column_names, self.supervised_column])
         
     '''
     To add internal spans to the next network span, we are going to use a stack of networl request that hold the index tuple for the matrix
     and will add the span onto the sum. Important to note that we will NOT increment the counter for that index tuple. Also we will not pop the element as normal rather peek. Given the
     possibility that two internal spans happen after each other. For this to work, we will also sort the spans of the trace after the starttime of the trace so eventaully every internal span will find
     a network parent, because frontend proxy will be invoked first.
     '''
     def gen_adf(self, single_trace_df : pd.DataFrame) -> list[list[tuple[int, float]]]:

          adjency_matrix = [[(0, 0.0) for _ in range(len(constants.SERVICES))] for _ in range(len(constants.SERVICES))]
          stack = []
          sorted = single_trace_df.sort_values(by=constants.START_TIME, ascending=True)

          for _ , row in sorted.iterrows():

               if row[constants.SPAN_KIND] == constants.INTERNAL_TYPE:
                    span_duration = row[constants.DURATION_COLUMN]
                    # peek the stack
                    if len(stack) > 0:
                         indices = stack[-1]
                         self.handle_internal_span(indices, adjency_matrix, span_duration)
                         continue
                    else:
                         continue

               ref_span_id = row[constants.REF_TYPE_SPAN_ID]

               if ref_span_id == constants.NOT_AVAILABLE:
                    #we have found the FE proxy invocation
                    continue
               ref_service_name = self._find_service_name_for_spanID(ref_span_id=ref_span_id, single_trace_df=single_trace_df)
               if ref_service_name == "":
                    # I am not sure when this happens, but it can happen
                    continue
               service_name = row[constants.SERVICE_NAME_COLUMN]
               duration = row[constants.DURATION_COLUMN]
               """row_ind is the client span , col_ind the server span --> [client , server] for the index tuple in the matric insertion"""
               try:
                    row_ind = constants.SERVICES[service_name]
                    col_ind = constants.SERVICES[ref_service_name]
               except Exception as e:
                    #print(f"ref_service_name or service_name : {ref_service_name}, {service_name} not found")
                    continue
               if adjency_matrix[row_ind][col_ind][0] == -1:
                    adjency_matrix[row_ind][col_ind] = (1 , duration)
               else:
                    tuple_val = adjency_matrix[row_ind][col_ind]
                    adjency_matrix[row_ind][col_ind] = (tuple_val[0] +1, tuple_val[1] + duration)
               stack.append([row_ind, col_ind])
               
          return adjency_matrix
     

     def handle_internal_span(self, indices : list[int], adjency_matrix : list[list[float]], span_duration : int):
          tuple_before = adjency_matrix[indices[0]][indices[1]]
          adjency_matrix[indices[0]][indices[1]] = (tuple_before[0], tuple_before[1] + span_duration)


     """find corresponding name for the parent span to generate index tuple"""
     def _find_service_name_for_spanID(self, ref_span_id : str, single_trace_df : pd.DataFrame) -> str:
          # sometimes spans reference other trace ids in the  --> this slows down speed tremendiously!!! (maybe just leave it out and save time)
          for _, row in single_trace_df.iterrows():
               if row[constants.SPAN_ID_COLUMN] == ref_span_id:
                   return row[constants.SERVICE_NAME_COLUMN]
          
          return ""

     '''This function just weights the '''
     def _weight_adjency_matrix(self, tuple_adj_matrix : list[list[tuple[int, float]]]) -> list[list[float]]:

          result = [[0.0 for _ in range(len(self.service_name_mapping))] for _ in range(len(self.service_name_mapping))]
          for row_index, row  in enumerate(tuple_adj_matrix):
               for col_index , col in enumerate(row):
                    sum_req_times = tuple_adj_matrix[row_index][col_index][1]
                    number_reqs = tuple_adj_matrix[row_index][col_index][0]
                    if number_reqs > 0:
                         result[row_index][col_index] = sum_req_times / number_reqs

          return result

     # since the data comes from one experiement with only ine injected fault
     def gen_one_hot_encoding_for_exp(self) -> list[float]:
          try:
               one_hot_values = [0.0] * (len(self.service_name_mapping) + 1)
               one_hot_values[self.injected_service] = 1
               return one_hot_values
          except KeyError as e:
               return []
     
     '''
     This function is creating the lower and upper bound for the performance anomaly detection per service tuple
     based on very simple "outlier detection". This could be up for discussion for improvements. For now I would leave it this way as stated in the paper.
     Here we use int as a val corresponding to the index in the flattened dataframe
     dict[m_n, [number of observations between MS m and n , average, variance ]]
     at another point in time we pool the variances with the assuption that the datasets are independent
 
     def get_bounds_for_service_calls(self) -> dict[str , float]:
          merged = [var.adf_matrices for var in self.variables]
          result = pd.concat(merged, axis=0, ignore_index=True)
          columns_for_average = self.column_names
          average_series = result[columns_for_average].mean()
          series_dict = average_series.to_dict()
          print(series_dict)
          self.weights_of_edges = series_dict

     '''

     '''
     I am using conditional probability here for calculating the KPI:
          P(trace has error code | faulty Trace)
          P(trace has no error code | faulty Trace)
          P(trace has error code | goody Trace)
          P(trace has no error code | goody Trace)
     '''
     def _calc_error_ratio_for_var(self, var : TraceResponseVariable) -> None:
          if var.adf_matrices is not None:
               faulty_traces_with_error = 0
               faulty_traces_no_error = 0
               good_traces_with_error = 0
               good_traces_no_error = 0
               # number of traces within the varibale
               len_goody_traces = len(var.adf_matrices[var.adf_matrices[self.supervised_column] == constants.NO_TREATMENT])
               len_faulty_traces = len(var.adf_matrices[var.adf_matrices[self.supervised_column] != constants.NO_TREATMENT])
               for _,row  in var.adf_matrices.iterrows():
                    if row[constants.ERROR_IN_TRACE_COLUMN] == 0 and row[self.supervised_column] == constants.NO_TREATMENT:
                         good_traces_no_error +=1
                    elif row[constants.ERROR_IN_TRACE_COLUMN] == 1 and row[self.supervised_column] == constants.NO_TREATMENT:
                         good_traces_with_error += 1 
                    elif row[constants.ERROR_IN_TRACE_COLUMN] == 0 and row[self.supervised_column] != constants.NO_TREATMENT:
                         faulty_traces_no_error += 1
                    elif row[constants.ERROR_IN_TRACE_COLUMN] == 1 and row[self.supervised_column] != constants.NO_TREATMENT:
                         faulty_traces_with_error +=1
               if len_faulty_traces > 0:
                    var.error_ratio[constants.FAULTY_ERROR] = faulty_traces_with_error / len_faulty_traces
                    var.error_ratio[constants.FAULTY_NO_ERROR] = faulty_traces_no_error / len_faulty_traces
               if len_goody_traces > 0:
                    var.error_ratio[constants.GOOD_ERROR] = good_traces_with_error / len_goody_traces
                    var.error_ratio[constants.GOOD_NO_ERROR] = good_traces_no_error / len_goody_traces


"""
if __name__=='__main__':
     
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
     
     for var in response_variables:
          print(var.data.head(5))
          print(var.data.columns)
     
     ex_label = handler.get_experiment_label("01737208087")
     
     con = RWDGController(response_variables, "01737208087",ex_label )
     
     con.iterate_over_varibales()
"""
