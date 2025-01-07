'''
In this file I am Training the Model based on the experiment Data.
 And store it so it can be accessed by other Components.
'''
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Callable
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader, random_split
import pandas as pd


class TraceModel(nn.Module):

     def __init__(self, loss_function : Callable,   dimensions : list[int], activations : list[Callable]):
          super(TraceModel, self).__init__()
          self.loss_function = loss_function
          # in the input layer there is no activation
          assert len(activations) == len(dimensions) -1
          self.activations = activations
          self.layers = self.init_model_layers(dimensions=dimensions)
     
     def init_model_layers(self, dimensions : list[int])-> nn.ModuleList:
          layers = nn.ModuleList()
          for idx in range(1, len(dimensions) -1):
               new_layer = nn.Linear(in_features=dimensions[idx -1],out_features=dimensions[idx],  bias=True)
               layers.append(new_layer)
          return layers

     def forward(self, input : torch.tensor) -> torch.tensor:
          for index in range(len(self.layers)):
               input = self.layers[index](input)
               input = self.activations[index](input)
          return input
     
     # for calculating the accuracies for batches during training
     def calculate_accuracy(self, predictions : torch.tensor, actual : torch.tensors) -> float:
          counter_acc = 0
          counter = 0
          for row in predictions:
               max_ind = torch.argmax(row)
               if max_ind == actual[counter]:
                    counter_acc += 1
               counter += 1
          
          return counter_acc / len(predictions)

     def train_trace_model(self, train_loader : DataLoader , iterations : int) -> tuple[list[float], list[float]]:
          # initlaized with the standard parameters
          optimizer = optim.Adam(self.parameters(), lr=0.001)

          errors = []
          accuracies = []
          iterations_counter = 0
          while iterations_counter < iterations:
                    for batch, labels in train_loader:
                         optimizer.zero_grad()
                         out =  self.forward(batch)
                         loss = self.loss_function(out, labels)
                         # just for vizualizing during training
                         if iterations_counter % 100 == 0:
                              accuracy = self.calculate_accuracy(out, labels)
                              accuracies.append(accuracy)
                              errors.append(loss.item())
                         loss.backward() 
                         optimizer.step()
                         iterations_counter += 1

          return errors, accuracies

     def save_model_dict(self, PATH) -> None: 
          #print(model.state_dict())
          torch.save(self.state_dict(), PATH)


