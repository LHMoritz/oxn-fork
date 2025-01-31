import zipfile

from fastapi import HTTPException
from backend.internal.analysis import ExperimentAnalyzer
from backend.internal.errors import StoreException
from backend.internal.fault_detection import PrometheusDetectionAnalyzer
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
import fcntl
import logging
from typing import Dict, Optional, Tuple, List
import pandas as pd
from backend.internal.engine import Engine
from backend.internal.kubernetes_orchestrator import KubernetesOrchestrator
from backend.internal.models.experiment import CreateBatchExperimentResponse, CreateExperimentResponse, Experiment, ExperimentStatus
from backend.internal.models.fault_detection import DetectionAnalysisResult
from backend.internal.prometheus import Prometheus
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

    def create_experiment(self, name, config: Experiment) -> CreateExperimentResponse:
        """Create new experiment directory and config file"""
        if not self.acquire_lock():
            logger.info("Lock already held.")
            raise Exception("Lock already held - cannot create experiment")
        try:
            experiment_id = str(self.counter) + str(int(time.time()))
            self.counter += 1
            logger.info(f"Creating experiment: {name} with ID: {experiment_id}")
            experiment = {
                'id': experiment_id,
                'name': name,
                'status': 'PENDING',
                'created_at': datetime.now().isoformat(),
                'started_at': "",
                'completed_at': "",
                'error_message': "",
                'spec': config.model_dump(mode="json"),
            }
            
            # Save experiment config
            self.store.save(f"{experiment_id}_config", experiment, FileFormat.JSON)
        finally:
            self.release_lock()
        return CreateExperimentResponse(**experiment)
    

    def create_batch_experiment(self, name: str, config: Experiment, parameter_variations: dict) -> CreateBatchExperimentResponse:
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
            'created_at': datetime.now().isoformat(),
            'started_at': "",
            'completed_at': "",
            'error_message': "",
            'spec': config.model_dump(mode="json"),
            'parameter_variations': parameter_variations,
        }

        self.store.save(f"{batch_id}_config", batch_config, FileFormat.JSON)

        # Create params_to_id.json mapping
        param_mapping = []
        all_parameter_combinations = list(dict_product(parameter_variations))
        
        for i, parameters in enumerate(all_parameter_combinations):
            # patch the config with the parameters
            logger.debug(f"parameters: {parameters}")
            sub_config = update_dict_with_parameter_variations(config.model_dump(mode="json"), parameters)

            sub_experiment = {
                'id': f"{i}",
                'name': f"{name}_{i}",
                'status': 'PENDING',
                'created_at': datetime.now().isoformat(),
                'started_at': "",
                'completed_at': "",
                'error_message': "",
                'spec': sub_config,
            }

            self.store.save(f"{batch_id}_{i}_config", sub_experiment, FileFormat.JSON)
                
            param_mapping.append({
                'sub_experiment_id': i,
                **parameters
            })

        # Save parameter mapping to JSON
        self.store.save(f"{batch_id}_params_to_id", param_mapping, FileFormat.JSON)
        
        return CreateBatchExperimentResponse(**batch_config)
    
    def get_experiment_config(self, experiment_id) -> Experiment:
        """Get experiment config"""
        experiment_config = self.store.load(f"{experiment_id}_config", FileFormat.JSON)
        if experiment_config is None:
            raise ValueError(f"No experiment config found for experiment {experiment_id}")
        if not isinstance(experiment_config, dict):
            raise ValueError(f"Experiment config is not a dictionary for experiment {experiment_id}")
        try:
            return Experiment(**experiment_config['spec'])
        except Exception as e:
            logger.error(f"could not load experiment config: {e}")
            raise e
        
    def get_experiment_status(self, experiment_id) -> ExperimentStatus:
        """Get experiment status file. Contains status, started_at, completed_at, error_message and the config"""
        experiment_config = self.store.load(f"{experiment_id}_config", FileFormat.JSON)
        if experiment_config is None:
            raise ValueError(f"No experiment config found for experiment {experiment_id}")
        if not isinstance(experiment_config, dict):
            raise ValueError(f"Experiment config is not a dictionary for experiment {experiment_id}")
        status = ExperimentStatus(
            id=experiment_id,
            name=experiment_config['name'],
            status=experiment_config['status'],
            started_at=experiment_config['started_at'],
            completed_at=experiment_config['completed_at'],
            error_message=experiment_config['error_message']
        )
        return status
    

    def run_batch_experiment(self, batch_id: str, output_formats: List[FileFormat], runs: int, analyse_fault_detection: bool = False):
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
                    if analyse_fault_detection:
                        # output data is stored - can be retrieved later using get_experiment_data
                        self.analyze_fault_detection(f"{batch_id}_{sub_experiment_id}")
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
    
    def run_experiment(self, experiment_id, output_formats:List[FileFormat], runs):
        """Run experiment"""
        if not self.acquire_lock():
            logger.info("Lock already held, skipping experiment check")
            return False
        try:
            logger.info(f"Changing experiment status to RUNNING")
            self.update_experiment_config(experiment_id, {'status': 'RUNNING'})
            logger.debug(f"experiment config: {self.get_experiment_config(experiment_id)}")
            experiment = self.get_experiment_config(experiment_id)
        
            engine = Engine(
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
                responses, report_data = engine.run(orchestration_timeout=120, randomize=False, accounting=False)
                
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
            raise e
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
        try:
            # Load the full config document first
            config_doc = self.store.load(f"{experiment_id}_config", FileFormat.JSON)
            if config_doc is None or not isinstance(config_doc, dict):
                raise ValueError(f"No valid experiment config found for experiment {experiment_id}")
                
            # Update the document with the new values
            config_doc.update(updates)
            
            # Save the updated config back to store
            self.store.save(f"{experiment_id}_config", config_doc, FileFormat.JSON)
        except Exception as e:
            logger.error(f"could not update experiment config: {e}")
            raise e
    
    def list_experiments_status(self, status_filter: Optional[str] = None, limit: int = 1000) -> List[ExperimentStatus]:
        """List all Status of all experiments"""
        all_documents = self.store.list_keys()
        experiments = []
        length = 0
        for document in all_documents:
            if document.endswith("_config"):  # Changed condition to look for config files
                experiment_config = self.store.load(document, FileFormat.JSON)
                if experiment_config is not None and isinstance(experiment_config, dict):
                    if status_filter is not None and experiment_config.get('status') != status_filter:
                        continue
                    length += 1
                    if length > limit:
                        break
                    # Extract only the fields needed for ExperimentStatus
                    status_data = {
                        'id': experiment_config.get('id', ""),
                        'name': experiment_config.get('name', ""),
                        'status': experiment_config.get('status', ""),
                        'started_at': experiment_config.get('started_at', ""),
                        'completed_at': experiment_config.get('completed_at', ""),
                        'error_message': experiment_config.get('error_message', "")
                    }
                    try:
                        experiments.append(ExperimentStatus(**status_data))
                    except Exception as e:
                        logger.error(f"could not create experiment status for {status_data}: {e}")
                        continue
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
    
    def get_analysis_data(self) -> Dict:
        """
        Retrieves analysis data from the configured analysis path
        
        Returns:
            Dict: Dictionary containing the analysis data from all JSON files
            
        Raises:
            HTTPException: If no data is found or if there's an error loading the data
        """
        analysis_path = os.getenv("OXN_ANALYSIS_PATH", "/mnt/analysis-datastore")
        
        try:
            # Check if path exists and contains data
            if not os.path.exists(analysis_path) or len(os.listdir(analysis_path)) == 0:
                raise HTTPException(
                    status_code=404, 
                    detail="No analysis data found"
                )
                
            # Load data from directory
            data = {}
            for filename in os.listdir(analysis_path):
                file_path = os.path.join(analysis_path, filename)
                if filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data[filename] = json.load(f)
                        
            return data
            
        except Exception as e:
            logger.error(f"Error loading analysis data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error loading analysis data: {str(e)}"
            )

    def save_detection_results(self, experiment_id: str, results: Dict, mechanism: str):
        """Save fault detection results for an experiment"""
        self.store.save(f"{experiment_id}_{mechanism}_detection", results, FileFormat.JSON)
        
    def analyze_fault_detection(self, experiment_id: str) -> List[DetectionAnalysisResult]:
        """Analyze fault detection for an experiment"""
        report = self.get_experiment_report(experiment_id)
        if report is None:
            raise ValueError(f"No report found for experiment {experiment_id}")
        
        # TODO find a place to keep a reference to the prometheus client
        experiment = self.get_experiment_config(experiment_id)
        if experiment is None:
            raise ValueError(f"No experiment config found for experiment {experiment_id}")
        orchestrator = KubernetesOrchestrator(experiment_config=experiment)
        prometheus_client = Prometheus(orchestrator, target="sue")
        prometheus_analyzer = PrometheusDetectionAnalyzer(prometheus_client)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        analyzer = ExperimentAnalyzer(
            detection_analyzer=prometheus_analyzer
        )
        detections = prometheus_analyzer.get_raw_detection_data(start_time, end_time)
        results = analyzer.analyze_fault_detection(report)

        serializable_results = [result.to_dict() for result in results]
        # Save detections
        self.store.save(
            f"{experiment_id}_detections",
            {'detections': detections},
            FileFormat.JSON
        )
        # Save results
        self.store.save(
        f"{experiment_id}_fault_detection",
        serializable_results,
        FileFormat.JSON
    )
        
        return results
        

    def get_experiment_fault_detection(self, experiment_id: str) -> List[DetectionAnalysisResult]:
        """Get fault detection for an experiment"""
        fault_detection_raw = self.store.load(f"{experiment_id}_fault_detection", FileFormat.JSON)
        if fault_detection_raw is None:
            raise ValueError(f"No fault detection found for experiment {experiment_id}")
        try:
            return [DetectionAnalysisResult(**result) for result in fault_detection_raw]   
        except Exception as e:
            logger.error(f"could not load fault detection: {e}")
            raise e
    
    def get_experiment_detections(self, experiment_id: str) -> dict:
        """Get raw detection data for an experiment"""
        detections = self.store.load(f"{experiment_id}_detections", FileFormat.JSON)
        if detections is None:
            raise ValueError(f"No detections found for experiment {experiment_id}")
        # This check needs to be changed if someone wants to store non-dict data for the raw detections
        if not isinstance(detections, dict):
            raise ValueError(f"Detections are not a dictionary for experiment {experiment_id}")
        return detections


        

