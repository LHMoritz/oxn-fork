'''
In this file I am Training the Model based on the experiment Data.
 And store it so it can be accessed by other Components.
'''
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Callable
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
import pandas as pd
import os


class TraceModel(nn.Module):

     def __init__(self, loss_function : Callable,   dimensions : list[int], activation : Callable):
          super(TraceModel, self).__init__()
          self.loss_function = loss_function
          self.activation = activation
          self.layers = self.init_model_layers(dimensions=dimensions)
          for lay in self.layers:
               print(f"input dim: {lay.in_features}")
               print(f"output dim: {lay.out_features}")
          print(len(self.layers))
          
          
     
     def init_model_layers(self, dimensions : list[int])-> nn.ModuleList:
          layers = nn.ModuleList()
          for idx in range(1, len(dimensions)):
               new_layer = nn.Linear(in_features=dimensions[idx -1],out_features=dimensions[idx],  bias=True)
               layers.append(new_layer)
          return layers

     def forward(self, input : torch.tensor) -> torch.tensor:
          for index in range(len(self.layers)):
               input = self.layers[index](input)
               input = self.activation(input)
          return input
     
     # for calculating the accuracies for batches during training and ultimately the report
     def calculate_accuracy(self, predictions : torch.tensor, actual : torch.tensor) -> float:
          counter_acc = 0
          counter = 0
          #print(actual)
          for x in range(len(predictions)):
               pred_row = predictions[x]
               actual_row = actual[x]
               #getting the indices
               max_ind_pred = torch.argmax(pred_row)
               max_ind_actual = torch.argmax(actual_row)
     
               if max_ind_pred == max_ind_actual:
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
                         print(f"Optimizing for batch with ID: {iterations_counter}")
                         optimizer.zero_grad()
                         out =  self.forward(batch)
                         #print(f"The output tensor: {out.shape}")
                         #print(f"the batch tensor : {batch.shape}")
                         #print(f"the labels tensor: {labels.shape}")
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
     
     def infer(self, input: torch.tensor )-> torch.tensor:
          input = self.forward(input)
          # dim 1 is important if the batch size > 1
          return nn.Softmax(input, dim=1)
     
     def test_trace_model(self, test_loader : DataLoader) -> tuple[list[float], list[float]]:
          error = []
          acc = []
          for batch , labels in test_loader:
               out = self.infer(batch)
               loss = self.loss_function(out, labels)
               error.append(loss.item())
               acc.append(self.calculate_accuracy(out, labels))
          
          return error , acc


     def save_model_dict(self, PATH) -> None: 
          #print(model.state_dict())
          torch.save(self.state_dict(), PATH)
     
def vizualize_training_err_and_acc(err : list[float], acc : list[float]) -> None:
     x_axis = list(range(len(err)))
     plt.plot(x_axis, err, label='Mean Error', marker='o')
     plt.plot(x_axis, acc , label='Accuracy', marker='x' )
     plt.title("Training")
     plt.legend()
     plt.show()

def vizualize_test_err_and_acc(err : list[float], acc : list[float]) -> None:
     x_axis = list(range(len(err)))
     plt.plot(x_axis, err, label='Mean Error', marker='o')
     plt.plot(x_axis, acc , label='Accuracy', marker='x' )
     plt.title("Test")
     plt.legend()
     plt.show()



