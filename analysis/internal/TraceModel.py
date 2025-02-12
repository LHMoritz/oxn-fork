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
from torcheval.metrics import MulticlassPrecision
import analysis.internal.constants as constants

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

     def calculate_precision_multiclass(self, predictions : torch.Tensor, targets: torch.Tensor) -> float:
          pred_labels = torch.argmax(predictions, dim=1)
          metric = MulticlassPrecision(average="micro", num_classes= (len(constants.SERVICES) +1))
          metric.update(pred_labels, targets)
          return metric.compute().item()
     


     """

          For Multiclass classification:

          Calculate per class accuracy for index:
          12 : recommendationservice
          16 : no fault injected
          
          As a third float we want to know the ratio of other predictions (every other index than 12 or 16) and this this changes over time.
          the third float in the tuple will be the ratio of number other class predictions (except 12 or 16) / batch size
                this will yield a ratio between [0, 1] and can easily be plotted with the precisions

     """
     def calculate_per_class_precision(self, predictions: torch.Tensor, labels: torch.Tensor) -> tuple[float, float, float]:
          pred_labels = torch.argmax(predictions, dim=1)


          recommendations_index = 12
          no_fault_index = 16

          predicted_recommendation_service = (pred_labels == recommendations_index)
          predicted_no_fault = (pred_labels == no_fault_index)


          predicted_other_classes = ((pred_labels != recommendations_index) & (pred_labels != no_fault_index)).sum().item()

          true_positives_recom = ((pred_labels == recommendations_index) & (labels == recommendations_index)).sum().item()
          true_positives_no_fault = ((pred_labels == no_fault_index) & (labels == no_fault_index)).sum().item()

          # Count the total predictions per class
          num_recom_predicted = predicted_recommendation_service.sum().item()
          num_predicted_no_fault = predicted_no_fault.sum().item()

          if num_recom_predicted > 0:
               recom_precision = float(true_positives_recom / num_recom_predicted)
          else:
               recom_precision = 0.0

          if num_predicted_no_fault > 0:
               no_fault_precision = float(true_positives_no_fault / num_predicted_no_fault)
          else:
               no_fault_precision = 0.0
          
          ratio_other_class_predictions = predicted_other_classes / len(pred_labels)

          return recom_precision, no_fault_precision , ratio_other_class_predictions



     def train_trace_model(self, train_loader : DataLoader , num_epochs : int) -> tuple[list[float], list[float]]:
          # initlaized with the standard parameters
          optimizer = optim.Adam(self.parameters(), lr=0.001)

          errors = []
          precison_per_batch_recom = []
          precison_per_batch_no_fault = []
          other_class_prediction_ratios = []
          for epoch in range(num_epochs):
                    precisions = []
                    for batch, labels in train_loader:
                         optimizer.zero_grad()
                         out =  self.forward(batch)
                         targets = torch.argmax(labels, dim=1)
                         loss = self.loss_function(out, targets)
                         # just for vizualizing during training
                         recom_precision, no_fault_precision, other_class_pred_ratio = self.calculate_per_class_precision(out, targets)
                         precison_per_batch_recom.append(recom_precision)
                         precison_per_batch_no_fault.append(no_fault_precision)
                         other_class_prediction_ratios.append(other_class_pred_ratio)
                         errors.append(loss.item())
                         loss.backward() 
                         optimizer.step()
                    
          logger.info("finished training")
          return precison_per_batch_recom, precison_per_batch_no_fault, other_class_prediction_ratios
     
     def infer(self, input: torch.Tensor )-> torch.Tensor:
          input = input.unsqueeze(0)
          input = self.forward(input)
          input = self.soft_max(input)
          return input
 
     
     def test_trace_model(self, test_loader : DataLoader) ->  list[float]:
          logger.info("starting testing the data")
          precison_recom_list = []
          precison_no_fault_list = []
          other_prediction_ratios  = []
          self.eval()
          with torch.no_grad():
               for batch , labels in test_loader:
                    #labels = labels.long()
                    out = self.forward(batch)
                    targets = torch.argmax(labels, dim=1)
                    precision_recom , precison_no_fault, other_class_ratios = self.calculate_per_class_precision(out, targets)
                    precison_recom_list.append(precision_recom)
                    precison_no_fault_list.append(precison_no_fault)
                    other_prediction_ratios.append(other_class_ratios)
          
          return precison_recom_list, precison_no_fault_list, other_prediction_ratios
     

     def calculate_tp_fp(self , preds: torch.Tensor, targets: torch.Tensor) -> tuple[int, int, int, int]:
         
          CLASS_RECOM = 12  
          CLASS_NO_FAULT = 16 
          tp_recom = ((preds == CLASS_RECOM) & (targets == CLASS_RECOM)).sum().item()
          tp_no_fault = ((preds == CLASS_NO_FAULT) & (targets == CLASS_NO_FAULT)).sum().item()
          fp_recom = ((preds == CLASS_RECOM) & (targets != CLASS_RECOM)).sum().item()
          fp_no_fault = ((preds == CLASS_NO_FAULT) & (targets != CLASS_NO_FAULT)).sum().item()

          return tp_recom, fp_recom, tp_no_fault, fp_no_fault

     def test_trace_model_precision(self,  test_loader : DataLoader) -> tuple[float, float]:
          logger.info("Starting model evaluation on test data")
          
          total_tp_recom, total_fp_recom = 0, 0
          total_tp_no_fault, total_fp_no_fault = 0, 0

          self.eval()
          with torch.no_grad():
               for batch, labels in test_loader:
                    out = self.forward(batch)
                    targets = torch.argmax(labels, dim=1)
                    preds = torch.argmax(out, dim=1)  # Get predicted class indices

                    # Compute per-class precision
                    tp_recom, fp_recom, tp_no_fault, fp_no_fault = self.calculate_tp_fp(preds, targets)

                    total_tp_recom += tp_recom
                    total_fp_recom += fp_recom
                    total_tp_no_fault += tp_no_fault
                    total_fp_no_fault += fp_no_fault

          # Compute overall precision for each class
          precision_recom = total_tp_recom / (total_tp_recom + total_fp_recom + 1e-10)
          precision_no_fault = total_tp_no_fault / (total_tp_no_fault + total_fp_no_fault + 1e-10)

          return precision_recom, precision_no_fault


     def save_model_dict(self, PATH) -> None: 
          #print(model.state_dict())
          torch.save(self.state_dict(), PATH)


def visualize_training_precision(precision_recom, precision_no_fault, other_prediction_ratio, training_or_test : str,   filename="training_precision.png", ):
   
    x_batches = np.arange(1, len(precision_recom) + 1)
    
    plt.figure(figsize=(10, 5))
    
    # Plot both time series on the same figure.
    plt.plot(x_batches, precision_recom, label='Precision Recom', alpha=0.7, marker='o')
    plt.plot(x_batches, precision_no_fault, label='Precision No Fault', alpha=0.7, marker='o')
    plt.plot(x_batches, other_prediction_ratio, label='Other pred. ratio', alpha=0.7, marker='o')
    
    plt.xlabel(f"{training_or_test} Step (Batch Number)")
    plt.ylabel("Precision")
    plt.title(f"{training_or_test} Precision per Batch")
    plt.legend()
    plt.grid(True)
    
    # Save the figure.
    plt.savefig(filename)
    plt.close()


def plot_average_precisions(avg_recom: float, avg_no_fault: float, filename: str):
    
    labels = ['Recommendationservice', 'No Fault injected']
    values = [avg_recom, avg_no_fault]

    fig, ax = plt.subplots()
    bars = ax.bar(labels, values)
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), 
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    ax.set_ylabel('Precision')
    ax.set_title('Average Test Precision per Class')
    
    plt.tight_layout()
    plt.savefig(filename)
    plt.close(fig)








