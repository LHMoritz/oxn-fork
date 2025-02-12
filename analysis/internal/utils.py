"""
Some utility functions I need in several classes
"""
import analysis.internal.constants as constants
from analysis.internal.TraceModel import TraceModel
import torch.nn as nn
import torch
from analysis.internal.exceptions import ServiceUnknown
import logging

logger = logging.getLogger(__name__)

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
     return result

"""
This function loads the Model
"""
def load_model() -> TraceModel:
     try:
          model = TraceModel(nn.CrossEntropyLoss(), constants.SMALL_MODEL_DIMENSIONS, nn.ReLU())
          state_dict = torch.load(constants.MODEL_PATH, weights_only=True)
          model.load_state_dict(state_dict)
          # set the model to Evaluation mode to infer on unseen data
          model.eval()
          logging.info("successfully deserialized the model from disk")
          return model
     except Exception as e:
          logger.error("Could not load serialzed trace model from disk, exiting process")
          exit(1)

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
          raise ServiceUnknown("ServiceName for the label is unknown")
