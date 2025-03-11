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

OXN_MOUNT = "./internal/oxn/trainData2"
ANALYSIS_MOUNT = "./internal/oxn/transformed2"
transformer_storage_handler = LocalStorageHandler(OXN_MOUNT, 'trainData', ANALYSIS_MOUNT)



"""
     For Experiment with ID: 41737545062 
          ==> Treatment : delay , 120 ms , Injected Service: recommendationservice
     
          
     For Experiment with ID (Batch 10 runs) : 01737547493
          ==> Treatment : delay , 120 ms , Injected Service : recommendationservice 

"""


"""
     Big Delay Model:
          11739368800 : recommendationservice
          21739370401 : checkoutservice
          31739371482 : adservice
          41739375644 : currencyservice
          51739376582 : emailservice
          61739377327 : featureflagservice
          71739378001 : frauddetectionservice
          81739378664 : frontend
          91739379442 : frontendproxy
          101739380200 : paymentservice
          121739381977 : cartservice
          131739382742 : accountingservice
          141739383580 : quoteservice
          151739384226 : shippingservice
          161739384974 : flagd

"""

if __name__=='__main__':
     transformer = DataTransformerAndAnalyzer(storage_handler=transformer_storage_handler)

     #transformer.transform_data("41737545062", "recommendationservice")
     #transformer.transform_data("01737547493", "recommendationservice")
     #transformer.check_imbalanced_data("41737545062")
     #transformer.check_imbalanced_data("01737547493")
     #transformer.train_model()
     #transformer.check_goody_faulty_traces()
     #transformer.get_error_entire_code_ratio()
     """
     transformer.transform_data("11739368800", "recommendationservice")
     transformer.transform_data("21739370401", "checkoutservice")
     transformer.transform_data("31739371482", "adservice")
     transformer.transform_data("41739375644", "currencyservice")
     transformer.transform_data("51739376582", "emailservice")
     transformer.transform_data("61739377327", "featureflagservice")
     transformer.transform_data("71739378001", "frauddetectionservice")
     transformer.transform_data("81739378664", "frontend")
     transformer.transform_data("91739379442", "frontendproxy")
     transformer.transform_data("101739380200", "paymentservice")
     transformer.transform_data("121739381977", "cartservice")
     transformer.transform_data("131739382742", "accountingservice")
     transformer.transform_data("141739383580", "quoteservice")
     transformer.transform_data("151739384226", "shippingservice")
     transformer.transform_data("161739384974", "flagd")

     """
     #transformer.train_model_big()
     #transformer.print_tracing_data(experiment_id="11739368800")
     #transformer.plot_json_data()
     transformer.vizualize_trainin_and_test()

     