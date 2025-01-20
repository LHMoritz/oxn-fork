"""
Some utility functions I need in several classes
"""
import constants
from TraceModel import TraceModel
import torch.nn as nn
import torch

def gen_one_hot_encoding_col_names() -> list[str]:
          a=  [f"S_{ind}" for ind in range(len(constants.SERVICES))]
          return a


"""builds the column names for all the response variables"""
def build_colum_names_for_adf_mat_df() -> list[str]:
     result = []
     for _ , out_val in constants.SERVICES.items():
          for _ , in_val in constants.SERVICES.items():
               result.append(f"{out_val}_{in_val}")

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