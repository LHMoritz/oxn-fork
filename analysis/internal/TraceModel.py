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
import logging
import numpy as np

logger = logging.getLogger(__name__)

class TraceModel(nn.Module):

     def __init__(self, loss_function : Callable,   dimensions : list[int], activation : Callable):
          super(TraceModel, self).__init__()
          self.loss_function = loss_function
          self.activation = activation
          self.layers : nn.ModuleList = self.init_model_layers(dimensions=dimensions)
          self.soft_max : nn.Module = nn.Softmax(dim=0)
          
          
     def init_model_layers(self, dimensions : list[int])-> nn.ModuleList:
          layers = nn.ModuleList()
          for idx in range(1, len(dimensions)):
               new_layer = nn.Linear(in_features=dimensions[idx -1],out_features=dimensions[idx],  bias=True)
               nn.init.normal_(new_layer.weight, mean=0.0, std=1.0)
               layers.append(new_layer)
          return layers

     def forward(self, input : torch.Tensor) -> torch.Tensor:
          #print(f"Input shape: {input.shape}")
          for layer in self.layers:
               input = layer(input) 
               input = self.activation(input)
               #print(f"After layer {layer}: {input.shape}")
          return input
     
     # for calculating the accuracies for batches during training and ultimately the report
     def calculate_accuracy(self, predictions: torch.Tensor, targets: torch.Tensor) -> float:
          pred_labels = torch.argmax(predictions, dim=1)
          #actual_labels = torch.argmax(labels, dim=1)
          logger.info(f"the pred_lables :  {pred_labels}")
          logger.info(f"the actual labels :{targets}")
          accuracy = (pred_labels == targets).float().mean().item()
          logger.info(f"accuracy: {accuracy}")
          return accuracy

     def train_trace_model(self, train_loader : DataLoader , num_epochs : int) -> tuple[list[float], list[float]]:
          # initlaized with the standard parameters
          optimizer = optim.Adam(self.parameters(), lr=0.001)

          errors = []
          accuracies_per_batch = []
          accuracies_per_epoch = []
          iterations_counter = 0
          for epoch in range(num_epochs):
                    accuracies = []
                    for batch, labels in train_loader:
                         optimizer.zero_grad()
                         out =  self.forward(batch)
                         targets = torch.argmax(labels, dim=1)
                         loss = self.loss_function(out, targets)
                         # just for vizualizing during training
                         accuracy = self.calculate_accuracy(out, targets)
                         accuracies.append(accuracy)
                         errors.append(loss.item())
                         loss.backward() 
                         optimizer.step()
                    
                    accuracies_per_batch.extend(accuracies)
                    mean_accuracy_per_epoch = sum(accuracies) / len(accuracies)
                    accuracies_per_epoch.append(mean_accuracy_per_epoch)
                    

          logger.info("finished training")
          return accuracies_per_epoch, accuracies_per_batch
     
     def infer(self, input: torch.Tensor )-> torch.Tensor:
          input = input.unsqueeze(0)
          input = self.forward(input)
          input = self.soft_max(input)
          return input
 
     
     def test_trace_model(self, test_loader : DataLoader) ->  list[float]:
          logger.info("starting testing the data")
          acc = []
          self.eval()
          with torch.no_grad():
               for batch , labels in test_loader:
                    #labels = labels.long()
                    out = self.forward(batch)
                    targets = torch.argmax(labels, dim=1)
                    acc.append(self.calculate_accuracy(out, targets))
          
          return acc


     def save_model_dict(self, PATH) -> None: 
          #print(model.state_dict())
          torch.save(self.state_dict(), PATH)




def visualize_training_acc_per_batch(acc_per_batch, acc_per_epochs):
    batches_per_epoch = len(acc_per_batch) / len(acc_per_epochs)
    x_batches = np.arange(1, len(acc_per_batch) + 1)
    x_epochs = np.arange(batches_per_epoch, len(acc_per_batch) + 1, batches_per_epoch)
    plt.figure(figsize=(10, 5))
    plt.plot(x_batches, acc_per_batch, label='Batch Accuracy', alpha=0.7)
    plt.plot(x_epochs, acc_per_epochs, label='Epoch Accuracy', marker='o', linestyle='--', color='red')
    
    plt.xlabel("Training Step (Batch Number)")
    plt.ylabel("Accuracy")
    plt.title("Training Accuracy per Batch and per Epoch 3 hidden layers")
    plt.legend()
    plt.grid(True)
    plt.savefig("training_error_all.png")
    plt.close()

def vizualize_test_acc(acc : list[float]) -> None:
     x_axis = list(range(len(acc)))
     plt.plot(x_axis, acc , label='Test Accuracy', marker='x')
     plt.title("Test accuracy per batch 3 hidden layers")
     plt.xlabel("Test Step (Batch Number)")
     plt.ylabel("Accuracy")
     plt.legend()
     plt.grid(True)
     plt.savefig("test_error_all.png")
     plt.close()







