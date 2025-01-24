"""
Some utility functions I need in several classes
"""
import internal.constants as constants
from internal.TraceModel import TraceModel
import torch.nn as nn
import torch
from internal.exceptions import ServiceUnknown


"""
Here we have to account for the case that there is no fault injected
"""
def gen_one_hot_encoding_col_names() -> list[str]:
          return [f"S_{ind}" for ind in range(len(constants.SERVICES) +1 )]
          


"""builds the column names for all the response variables"""
def build_colum_names_for_adf_mat_df() -> list[str]:
     result = []
     for _ , out_val in constants.SERVICES.items():
          for _ , in_val in constants.SERVICES.items():
               result.append(f"{out_val}_{in_val}")

     #result.append(constants.ERROR_IN_TRACE_COLUMN)
     #print(result)
     return result

"""
This function loads the Model
"""
def load_model() -> TraceModel:
     model = TraceModel(nn.CrossEntropyLoss(), constants.MODEL_DIMENSIONS, nn.ReLU())
     state_dict = torch.load(constants.MODEL_PATH, weights_only=True)
     model.load_state_dict(state_dict)
     # set the model to Evaluation mode to infer on unseen data
     model.eval()
     return model

def get_treatment_column(column_names : list[str]) -> str:
     for col in column_names:
           if "treatment" in col:
                 return col
     
     return ""

def get_index_for_service_label(label : str) -> int:
     try:
          index : int = constants.SERVICES[label]
          return index
     except KeyError as e:
           raise ServiceUnknown("Service for the label is unknown")


if __name__=='__main__':
     build_colum_names_for_adf_mat_df()
     a = get_treatment_column(['index', 'trace_id', 'span_id', 'operation', 'start_time', 'end_time',
       'duration', 'service_name', 'span_kind', 'req_status_code', 'ref_type',
       'ref_type_span_ID', 'ref_type_trace_ID', 'add_security_context',
       'loss_treatment'])
     print(a)