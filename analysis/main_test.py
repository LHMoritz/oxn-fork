"""
Since, the program is heavily dependent on the on the input data. I will write some test using a mock database basically.
"""

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from analysis.internal.AnalysisManager import AnalysisManager
from analysis.internal.utils import load_model
from analysis.internal.StorageClient import LocalStorageHandler
import logging



logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

OXN_MOUNT = "./internal/oxn"
ANALYSIS_MOUNT = "./analyis/internal/oxn"
trace_model = load_model()
storage_handler = LocalStorageHandler(OXN_MOUNT, OXN_MOUNT)


# ex_id : "01737208087"
def test_normal_case_with_two_variables(experiment_id) -> None:

     try:
          logger.info(f"starting experiment with id {experiment_id}")
          analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
          analysis_manager.analyze_experiment()
     
     except Exception as e:
          logger.error(str(e))
     

# ex_id : 41737545062
def test_normal_ase_with_severa_random_varibales(experiment_id) -> None:
     try:
          logger.info(f"starting experiment with id {experiment_id}")
          analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
          analysis_manager.analyze_experiment()
     
     except Exception as e:
          logger.error(str(e))

# ex_id : 1234567843
def test_wrong_ex_id(experiment_id) -> None:
     try:
          logger.info(f"starting experiment with id {experiment_id}")
          analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
          analysis_manager.analyze_experiment()
     
     except Exception as e:
          logger.error(str(e))

# ex_id: 01737200116
def test_no_config_present(experiment_id) -> None:
     try:
          logger.info(f"starting experiment with id {experiment_id}")
          analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
          analysis_manager.analyze_experiment()
     
     except Exception as e:
          logger.error(str(e))

def test_no_data_present(experiment_id) -> None:
     try:
          logger.info(f"starting experiment with id {experiment_id}")
          analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
          analysis_manager.analyze_experiment()
     
     except Exception as e:
          logger.error(str(e))

# ex_id: 1999
def test_no_label_present_in_config(experiment_id) -> None:
     try:
          logger.info(f"starting experiment with id {experiment_id}")
          analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
          analysis_manager.analyze_experiment()
     
     except Exception as e:
          logger.error(str(e))

# ex_id : 
def test_data_for_ex_also_inlcudes_metrics(experiment_id) -> None:
     try:
          logger.info(f"starting experiment with id {experiment_id}")
          analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
          analysis_manager.analyze_experiment()
     
     except Exception as e:
          logger.error(str(e))

def test_batch_experiments_not_supported(experiment_id) -> None:
     try:
          logger.info(f"starting experiment with id {experiment_id}")
          analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
          analysis_manager.analyze_experiment()
     
     except Exception as e:
          logger.error(str(e))



#test_normal_case_with_two_variables(experiment_id="01737208087")
#test_normal_ase_with_severa_random_varibales("41737545062")
#test_no_config_present("01737200116")
#test_no_data_present("62864836929")
#test_no_label_present_in_config("1999")
#test_batch_experiments_not_supported("01737200116")







