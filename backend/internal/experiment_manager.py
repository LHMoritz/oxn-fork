import zipfile
import yaml
from backend.internal.errors import StoreException
from backend.internal.models.response import ResponseVariable
from fastapi import HTTPException
from pathlib import Path
import json
import time
from datetime import datetime
import fcntl
import logging
from fastapi.responses import FileResponse
from typing import Dict, Optional, Tuple, List
import pandas as pd
from backend.internal.engine import Engine
from backend.internal.kubernetes_orchestrator import KubernetesOrchestrator
from backend.internal.utils import dict_product, update_dict_with_parameter_variations
from backend.internal.store import DocumentStore, FileFormat
import io
import os
import requests
logger = logging.getLogger(__name__)
"""
Experiment Config filename : <experiment_id>_config.json
Experiment Report filename : <experiment_id>_report.yaml
Experiment Responses filename : <experiment_id>_<run_idx>_<response_name>.json / .csv

Batch Experiment Config filename : <batch_id>_config.json
Batch Sub Experiment Config filename : <batch_id>_<sub_experiment_id>_config.json
Batch Sub Experiment Report filename : <batch_id>_<sub_experiment_id>_report.yaml
Batch Sub Experiment Responses filename : <batch_id>_<sub_experiment_id>_<run_idx>_<response_name>.json / .csv
Batch Experiment Params to ID filename : <batch_id>_params_to_id.json
"""

class ExperimentManager:
    store: DocumentStore
    def __init__(self, base_path: Path, store: DocumentStore):
        self.base_path = base_path
        self.experiments_dir = self.base_path / 'experiments'
        self.lock_file = self.base_path / '.lock'
        self.counter = 0
        self.store = store
        
        # Ensure directories exist
        self.experiments_dir.mkdir(parents=True, exist_ok=True)

    def create_experiment(self, name, config):
        """Create new experiment directory and config file"""
        if not self.acquire_lock():
            logger.info("Lock already held, skipping experiment check")
            return False
        try:
            experiment_id = str(self.counter) + str(int(time.time()))
            self.counter += 1
            logger.info(f"Creating experiment: {name} with ID: {experiment_id}")
            experiment = {
                'id': experiment_id,
                'name': name,
                'status': 'PENDING',
                'created_at': datetime.now().isoformat(),
                'started_at': None,
                'completed_at': None,
                'error_message': None,
                'spec': config,
            }
            
            # Save experiment config
            self.store.save(f"{experiment_id}_config", experiment, FileFormat.JSON)
        finally:
            self.release_lock()
        return experiment
    

    def create_batch_experiment(self, name: str, config: dict, parameter_variations: dict):
        """
        Create a new batch experiment
        """

        batch_id = f"batch_{str(self.counter)}{int(time.time())}"
        self.counter += 1

        logger.info(f"Creating batch experiment: {name} with ID: {batch_id}")
        batch_config = {
            'id': batch_id,
            'name': name,
            'status': 'PENDING',
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'error_message': None,
            'spec': config,
            'parameter_variations': parameter_variations,
        }

        self.store.save(f"{batch_id}_config", batch_config, FileFormat.JSON)

        # Create params_to_id.json mapping
        param_mapping = []
        all_parameter_combinations = list(dict_product(parameter_variations))
        
        for i, parameters in enumerate(all_parameter_combinations):
            # patch the config with the parameters
            logger.debug(f"parameters: {parameters}")
            sub_config = update_dict_with_parameter_variations(config, parameters)

            sub_experiment = {
                'id': f"{i}",
                'name': f"{name}_{i}",
                'status': 'PENDING',
                'created_at': datetime.now().isoformat(),
                'started_at': None,
                'completed_at': None,
                'error_message': None,
                'spec': sub_config,
            }

            self.store.save(f"{batch_id}_{i}_config", sub_experiment, FileFormat.JSON)
                
            param_mapping.append({
                'sub_experiment_id': i,
                **parameters
            })

        # Save parameter mapping to JSON
        self.store.save(f"{batch_id}_params_to_id", param_mapping, FileFormat.JSON)
        
        return batch_config
    
    def get_experiment_config(self, experiment_id):
        """Get experiment config"""
        return self.store.load(f"{experiment_id}_config", FileFormat.JSON)
    
    def run_batch_experiment(self, batch_id: str, output_formats: List[str], runs: int):
        """Run a batch experiment"""
        try:
            logger.info(f"Running batch experiment: {batch_id}")
            self.update_experiment_config(batch_id, {'status': 'RUNNING'})

            params_to_id = self.store.load(f"{batch_id}_params_to_id", FileFormat.JSON)
            if params_to_id is None:
                logger.error(f"No params_to_id found for batch experiment {batch_id}")
                return
            total_sub_experiments = len(params_to_id)
            logger.info(f"Total sub experiments: {total_sub_experiments}")
            
            for params in params_to_id:
                sub_experiment_id = params['sub_experiment_id']
                try:
                    logger.info(f"Running sub experiment {sub_experiment_id} with params: {params}")
                    self.run_experiment(f"{batch_id}_{sub_experiment_id}", output_formats, runs)
                except Exception as e:
                    logger.error(f"Error running sub experiment {sub_experiment_id}: {e}")
                    raise e
                
            
        except Exception as e:
            logger.error(f"Error running batch experiment: {e}")
            self.update_experiment_config(batch_id, {'status': 'FAILED', 'error_message': str(e)})
        finally:
            pass



    def get_experiment_report(self, experiment_id):
        """Get experiment report"""
        return self.store.load(f"{experiment_id}_report", FileFormat.YAML)
    
    def run_experiment(self, experiment_id, output_formats, runs):
        """Run experiment"""
        if not self.acquire_lock():
            logger.info("Lock already held, skipping experiment check")
            return False
        try:
            logger.info(f"Changing experiment status to RUNNING")
            self.update_experiment_config(experiment_id, {'status': 'RUNNING'})
            logger.debug(f"experiment config: {self.get_experiment_config(experiment_id)}")
            experiment = self.get_experiment_config(experiment_id)['spec']

            orchestrator = KubernetesOrchestrator(experiment_config=experiment)
        
            engine = Engine(
                orchestrator_class=orchestrator,
                spec=experiment,
                id=experiment_id
            )
            report_data = {}
            for idx in range(runs):
                # report contains different run keys for each run.
                # A mismatch here: the report data is stored in a dict with run keys, but the response data is stored in a dict with response names
                # that are run specific.
                # Multiple calls to run() will keep on adding to the report data, so we only care about this object when we are done with all runs.
                # In contrast, we care about the response data for each run, so we need to write it to disk immediately.
                responses, report_data = engine.run(orchestration_timeout=None, randomize=False, accounting=False)
                
                for _ , response in responses.items():
                    # construct key
                    key = f"{experiment_id}_{idx}_{response.name}"
                    if response.data is not None:
                        if isinstance(response.data, pd.DataFrame):
                            response.data = response.data.to_dict(orient='records')
                        self.store.save(key, response.data, FileFormat.JSON)
                    else:
                        logger.error(f"response data is None for {response.name}")

            self.store.save(f"{experiment_id}_report", report_data, FileFormat.YAML)
            # Call the analysis service here
            self.call_analysis_service(experiment_id)

        except Exception as e:
            logger.error(f"Error running experiment: {e}")
            import traceback
            logger.error(f"stacktrace: {traceback.format_exc()}")
            self.update_experiment_config(experiment_id, {'status': 'FAILED', 'error_message': str(e)})
        finally:
            self.update_experiment_config(experiment_id, {'status': 'COMPLETED'})
            self.release_lock()

    def call_analysis_service(self, experiment_id: str) -> None:
        """Calls the analysis service to analyze the experiment results"""
        try:
            analysis_url = os.getenv("ANALYSIS_URL", "http://analysis-module:8001")
            response = requests.get(
                f"{analysis_url}/analyze",
                params={"experiment_id": experiment_id}
            )
            
            if response.status_code != 200:
                logger.error(f"Error calling analysis service: {response.status_code}")
                return
                
            logger.info(f"Analysis service successfully called for experiment {experiment_id}")
            
        except Exception as e:
            logger.error(f"Error calling analysis service: {str(e)}")


    def update_experiment_config(self, experiment_id, updates):
        """Update experiment config"""
        experiment_config = self.get_experiment_config(experiment_id)
        try:
            experiment_config.update(updates)
            self.store.save(experiment_id, experiment_config, FileFormat.JSON)
        except Exception as e:
            logger.error(f"could not update experiment config: {e}")
        

    def list_experiments(self):
        """List all experiments"""
        all_documents = self.store.list_keys()
        experiments = {}
        for document in all_documents:
            if document.endswith("_config"):
                experiment_config = self.store.load(document, FileFormat.JSON)
                if experiment_config is not None and isinstance(experiment_config, dict):
                    experiments[document] = experiment_config
        return experiments
    
    def list_experiments_status(self):
        """List all Status of all experiments"""
        all_documents = self.store.list_keys()
        experiments = {}
        for document in all_documents:
            if not document.endswith("_config"):
                experiment_config = self.store.load(document, FileFormat.JSON)
                if experiment_config is not None and isinstance(experiment_config, dict):
                    experiments[document] = experiment_config
        return experiments
    

    def acquire_lock(self):
        """File-based locking using fcntl"""
        try:
            # store the lock file path as an instance variable if not already open
            if not hasattr(self, 'lock_fd'):
                self.lock_fd = open(self.lock_file, 'w')
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            return False  # lock is held
        except (IOError, BlockingIOError):
            return False

    def release_lock(self):
        """Release file lock"""
        if hasattr(self, 'lock_fd'):
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            self.lock_fd.close()
            delattr(self, 'lock_fd')
    
    def get_experiment_response_data(self,run: int, experiment_id: str, response_name: str, file_ending: str):
        documents = self.store.list_keys()
        for document in documents:
            if document.endswith(f"{experiment_id}_{run}_{response_name}.{file_ending}"):
                return self.store.load(document, FileFormat.JSON)
        return None
    
    def get_experiment_data(self, experiment_id: str) -> io.BytesIO:
        files = self.store.list_files()
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=7) as zipf:
            for document in files:
                if document.startswith(f"{experiment_id}_"):
                    # Get data from the store and determine format
                    format = FileFormat.JSON
                    if document.endswith('.csv'):
                        format = FileFormat.CSV
                    elif document.endswith('.yaml'):
                        format = FileFormat.YAML
                    elif document.endswith('.json'):
                        format = FileFormat.JSON
                
                    data = self.store.load(document.rsplit('.', 1)[0], format)
                    if data is not None:
                        
                        if isinstance(data, (dict, list)):
                            data = json.dumps(data, default=str).encode('utf-8')
                        elif isinstance(data, str):
                            data = data.encode('utf-8')
                        # Write the data directly to the zip file with original filename
                        zipf.writestr(f"{document}", data)
        memory_zip.seek(0)
        return memory_zip
    
    def get_batched_experiment_id_by_params(self, batch_id: str, params: dict) -> Optional[str]:
        '''gets the experiment id for a given batch id and parameter combination'''
        id_mapping = self.store.load(f"{batch_id}_params_to_id", FileFormat.JSON)
        if id_mapping is None:
            logger.error(f"No id_mapping found for batch experiment {batch_id}")
            raise StoreException(f"No id_mapping found for batch experiment {batch_id}")
        
        for mapping in id_mapping:
            # Check if all params match the current mapping
            # (excluding sub_experiment_id from comparison)
            mapping_without_id = {k: v for k, v in mapping.items() 
                                if k != 'sub_experiment_id'}
            if mapping_without_id == params:
                return str(mapping['sub_experiment_id'])
            
        raise KeyError(f"parameter combination not found for batch experiment {batch_id}")
    
    def get_batched_experiment_report(self, batch_id: str, sub_experiment_id: str):
        '''gets the report for a given batch id and sub experiment id'''
        key = f"{batch_id}_{sub_experiment_id}_report"
        return self.store.load(key, FileFormat.YAML)
        
        
    def get_batched_experiment_response_data(self, batch_id: str, sub_experiment_id: str, response_name: str, file_ending: str):
        '''gets the response data for a given batch id and sub experiment id'''
        key = f"{batch_id}_{sub_experiment_id}_{response_name}.{file_ending}"
        return self.store.load(key, FileFormat.JSON)
        


        

