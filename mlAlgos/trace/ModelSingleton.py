'''
This class Ensure that the Microservice upon deployment has the model Loaded Preferrably in the main.py file where the webserver sits and can get passed
to the ModelController every time a new Experiment is exstantiated
'''
from TraceModel import TraceModel
import torch
import constants
import torch.nn as nn

class ModelSingleton(object):

     _model_instance : TraceModel = None

     def __init__(self):
          raise RuntimeError("Should not call Singleton Constructor -> call instance()")
     
     @classmethod
     def instance(cls) -> TraceModel:
          if cls._model_instance is None:
               model = TraceModel(nn.CrossEntropyLoss(), constants.MODEL_DIMENSIONS, nn.ReLU)
               state_dict = torch.load(constants.MODEL_PATH, weights_only=True)
               model.load_state_dict(state_dict)
               # set the model to Evaluation mode to infer on unseen data
               model.eval()
               cls._model_instance = model
          
          return cls._model_instance
     
