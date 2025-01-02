
from TraceResponseVariable import TraceResponseVariable
import pandas as pd
import constants
import numpy as np

'''
This class Takes in  a dataframe from with distributed tracing data and generates a dataframe
with 'adjency matrices' for each trace that captures the average response times between services.
It is part of the RWDG Trace model and therefore part for the data wranglin for the Multilayer perceptron.
'''

# TODO : interesting KPI: how many faulty traces do have error fields in there
# TODO : how much do the distribution differ from each other between fault and not fault?

# TODO: do we have a error in the trace -> 0 No , 1 yes 
# TODO : add internal spans to the next parent there

def mean_normalization( val : float, mean: float, min: float , max : float) -> float:
          nominator = val - mean
          denominator = max - min
          return nominator / denominator



class RWDGController:

     def __init__(self, variables : list[TraceResponseVariable], experiment_id, allowed_standard_deviation : str, injected_service: str):
          self.variables : list[TraceResponseVariable] = variables
          self.experiment_id : str = experiment_id
          self.weights_of_edges : dict[str, float] = None
          self.standard_deviation = allowed_standard_deviation
          self.service_name_mapping : dict[str , int] = constants.SERVICES # TODO change later to call a route on that
          self.service_name_mapping_backward = constants.SERVICES_REVERSE
          self.column_names = self._build_colum_names_for_adf_mat_df()
          self.injected_service = injected_service
          self.one_hot_encoding_for_exp = self.gen_one_hot_encoding_for_exp()
          self.one_hot_encoding_column_names = self.gen_one_hot_encoding_col_names()

     '''Normalizes the calculated weight matrices after the mean normalization
          This has the affect that each value is in range [0, 1] '''
     def normalizes_response_variables(self):
          min_values = []
          max_values = []
          avg_values = []
          result = pd.concat([var.adf_matrices for var in self.variables], ignore_index=True)
          for col in self.column_names:
               min_values.append(result[col].min())
               max_values.append(result[col].max())
               avg_values.append( result[col].mean())
          
          for var in self.variables:
               for idx in range(len(self.column_names)):
                    var.adf_matrices[self.column_names[idx]].apply(mean_normalization, args=(avg_values[idx], min_values[idx], max_values[idx]))

     
     def _calc_adf_matrices_for_variables(self)-> None:
          for var in self.variables:
               self._adj_mat_for_var(var)
     
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
               new_row.extend(self.one_hot_encoding_for_exp)
               dataframe_rows.append(new_row)
          
          # unpack the colum names
          '''Microservice name is here important. Later on we are going to merge the dataframes for each response variable and we still wan to have a direct mapping towards a service '''
          '''[trace_id, flattened_out weighted adj matrix, microservice_name, treatment yes / no]'''
          response_variable.adf_matrices = pd.DataFrame(dataframe_rows , columns=[constants.TRACE_ID_COLUMN, *self.column_names, "microservice_name",  *self.one_hot_encoding_column_names])
         # return pd.DataFrame(dataframe_rows , columns=[constants.TRACE_ID_COLUMN, *self.column_names, "microservice_name",  constants.SUPERVISED_COLUMN])

     def gen_adf(self, single_trace_df : pd.DataFrame) -> list[list[tuple[int, float]]]:

          adjency_matrix = [[(0, 0.0) for _ in range(len(constants.SERVICES))] for _ in range(len(constants.SERVICES))]
          #sorted = single_trace_df.sort_values(by=constants.START_TIME, ascending=True)

          for _ , row in single_trace_df.iterrows():

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
                    print(f"ref_service_name or service_name : {ref_service_name}, {service_name} not found")
                    continue
               #print(f"row_ind : {row_ind} col_ind : {col_ind}")
               #print(f"service_name: {service_name} ref_service_name : {ref_service_name}")
               if adjency_matrix[row_ind][col_ind][0] == -1:
                    adjency_matrix[row_ind][col_ind] = (1 , duration)
               else:
                    tuple_val = adjency_matrix[row_ind][col_ind]
                    adjency_matrix[row_ind][col_ind] = (tuple_val[0] +1, tuple_val[1] + duration)
               
          return adjency_matrix

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
               index = self.service_name_mapping[self.injected_service]
               one_hot_values = [0.0] * len(self.service_name_mapping)
               one_hot_values[index] = 1
               return one_hot_values
          except KeyError as e:
               pass
     
     def gen_one_hot_encoding_col_names(self) -> list[str]:
          return [f"S_{ind}" for ind in range(len(self.service_name_mapping))]

     
     '''
     This function is creating the lower and upper bound for the performance anomaly detection per service tuple
     based on very simple "outlier detection". This could be up for discussion for improvements. For now I would leave it this way as stated in the paper.
     Here we use int as a val corresponding to the index in the flattened dataframe
     dict[m_n, [number of observations between MS m and n , average, variance ]]
     at another point in time we pool the variances with the assuption that the datasets are independent
     '''
     def get_bounds_for_service_calls(self) -> dict[str , float]:
          merged = [var.adf_matrices for var in self.variables]
          result = pd.concat(merged, axis=0, ignore_index=True)
          columns_for_average = self.column_names
          average_series = result[columns_for_average].mean()
          series_dict = average_series.to_dict()
          print(series_dict)
          self.weights_of_edges = series_dict

     
     '''Lables all response variables, if there is a performance anomaly in the given span'''
     #TODO interesing to show how many actual performance anomalies are labeled for the 
     def label_performance_anomalies(self) -> None:
          pass

     #TODO interesting to show how good this actually is.
     '''
          A note here: they label the data artificially. OXN does that for us.
          it would be interesting to show that how much this artificial labeling through request times is actually good. So we can make here a 
     '''
     def _cruch_the_numbers(self):
          pass

     """builds the column names for all the response variables"""
     def _build_colum_names_for_adf_mat_df(self) -> list[str]:
          result = []
          for _ , out_val in constants.SERVICES.items():
               for _ , in_val in constants.SERVICES.items():
                    result.append(f"{out_val}_{in_val}")

          return result


if __name__ == "__main__":
     '''
     data = pd.read_csv("data/experiment_data/cartservice_traces.csv",  keep_default_na=False)
     controller = RWDGController(None, None, None, None)
     group_df = data.groupby(constants.TRACE_ID_COLUMN)
     for group_name, group_data in group_df:
          print(group_data[["service_name", "span_kind", "ref_type_span_ID", "duration", "span_id","ref_type", "trace_id", "start_time"]].sort_values(by=constants.START_TIME, ascending=True))
          print(controller.gen_adf(single_trace_df=group_data))
          break
     
     '''
     data = pd.read_csv("data/experiment_data/cartservice_traces.csv",  keep_default_na=False)
     var = TraceResponseVariable(data, 1, "bla")
     controller = RWDGController(None, None, None, None)
     print(controller._adj_mat_for_var(var).head(10))
     

     '''
     group_df = data.groupby(constants.TRACE_ID_COLUMN)
     for group_name, group_data in group_df:
          df_sorted_decending = group_data.sort_values(by='start_time', ascending=False)
          df_sorted_ascending = group_data.sort_values(by='start_time', ascending=True)
          endtime_df = group_data.sort_values(by='start_time', ascending=False)

          print(df_sorted_ascending[["service_name", "span_kind", "ref_type_span_ID", "duration", "span_id","ref_type", "trace_id"]])
          print("---------------------")
          print(df_sorted_decending[["service_name", "span_kind", "ref_type_span_ID", "duration", "span_id", "ref_type", "trace_id", "ref_type_trace_ID"]])
          print("---------------------")
          print(endtime_df[["service_name", "span_kind", "ref_type_span_ID", "duration", "span_id", "ref_type", "trace_id", "ref_type_trace_ID"]])
          break
     '''






     


     

     




     

     

     

