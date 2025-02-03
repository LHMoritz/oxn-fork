import sys
import os
from torch.utils.data import DataLoader

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from analysis.internal.DataTransformer import DataTransformerAndAnalyzer
from analysis.internal.StorageClient import LocalStorageHandler
import logging
from analysis.internal.TraceModel import TraceModel



logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

OXN_MOUNT = "./internal/oxn"
ANALYSIS_MOUNT = "./internal/oxn/transformed"
transformer_storage_handler = LocalStorageHandler(OXN_MOUNT, 'trainData', ANALYSIS_MOUNT)



"""
     For Experiment with ID: 41737545062 
          ==> Treatment : delay , 120 ms , Injected Service: recommendationservice
     
          
     For Experiment with ID (Batch 10 runs) : 01737547493
          ==> Treatment : delay , 120 ms , Injected Service : recommendationservice 

"""

if __name__=='__main__':
     transformer = DataTransformerAndAnalyzer(storage_handler=transformer_storage_handler)

     #transformer.transform_data("41737545062", "recommendationservice")
     #transformer.transform_data("01737547493", "recommendationservice")
     #transformer.check_imbalanced_data("41737545062")
     #transformer.check_imbalanced_data("01737547493")
     transformer.train_model()


     