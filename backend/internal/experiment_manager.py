
import zipfile
import yaml
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

logger = logging.getLogger(__name__)
logger.info = lambda message: print(message)
logger.error = lambda message: print(message)
logger.warning = lambda message: print(message)
logger.debug = lambda message: print(message)

class ExperimentManager:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.experiments_dir = self.base_path / 'experiments'
        self.lock_file = self.base_path / '.lock'
        self.counter = 0
        
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
            experiment_dir = self.experiments_dir / experiment_id
            logger.info(f"Creating experiment: {name} with ID: {experiment_id}")
            logger.info(f"Experiment Directory: {experiment_dir}")
            experiment = {
                'id': experiment_id,
                'name': name,
                'status': 'PENDING',
                'created_at': datetime.now().isoformat(),
                'started_at': None,
                'completed_at': None,
                'error_message': None,
                'spec': config,
                'paths': {
                    'data': str(experiment_dir / 'data'),
                    'benchmark': str(experiment_dir / 'benchmark'),
                    'report': str(experiment_dir / 'report')
                }
            }
            
            # Create directories
            experiment_dir.mkdir(parents=True)
            (experiment_dir / 'data').mkdir()
            (experiment_dir / 'benchmark').mkdir()
            (experiment_dir / 'report').mkdir()
            
            # Save experiment config
            with open(experiment_dir / 'experiment.json', 'w') as f:
                json.dump(experiment, f, indent=2)
        finally:
            self.release_lock()
        return experiment
    

    def create_batch_experiment(self, name: str, config: dict, parameter_variations: dict):
        """
        Create a new batch experiment

        experiments/
        └── batch_experiment_id/
            ├── experiment.json           # Batch metadata
            ├── params_to_id.csv         # Mapping of parameter combinations to experiment IDs
            ├── runs/
            │   ├──0/              # One directory per parameter combination
            │   │   ├── experiment.json     # Specific configuration for this run
            │   │   ├── data/
            │   │   └── report/
            │   ├──1/
            │   └──n/
        
        parameter_variations example:
        {
            "experiment.treatments.0.params.duration": ["1m", "2m", "3m"],
            "experiment.treatments.0.params.delay": [10, 20, 30]
        }
        """

        batch_id = f"batch_{str(self.counter)}{int(time.time())}"
        batch_dir = self.experiments_dir / batch_id
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
        
        # Create directory structure
        batch_dir.mkdir(parents=True)
        (batch_dir / 'runs').mkdir()

        # Create params_to_id.csv mapping
        param_mapping = []
        all_parameter_combinations = list(dict_product(parameter_variations))
        
        for i, parameters in enumerate(all_parameter_combinations):
            sub_experiment_dir = batch_dir / 'runs' / str(i)
            sub_experiment_dir.mkdir()

            # create data and report directories
            (sub_experiment_dir / 'data').mkdir()
            (sub_experiment_dir / 'report').mkdir()

            # patch the config with the parameters
            logger.debug(f"parameters: {parameters}")
            sub_config = update_dict_with_parameter_variations(config, parameters)

            with open(sub_experiment_dir / 'experiment.json', 'w') as f:
                json.dump(sub_config, f, indent=2)
                
            # Add mapping entry
            param_mapping.append({
                'sub_experiment_id': i,
                **parameters
            })

        # Save parameter mapping to CSV
        param_df = pd.DataFrame(param_mapping)
        param_df.to_csv(batch_dir / 'params_to_id.csv', index=False)

        # Save batch config
        with open(batch_dir / 'experiment.json', 'w') as f:
            json.dump(batch_config, f, indent=2)
        
        return batch_config
    
    def get_experiment(self, experiment_id):
        """Get experiment config"""
        try:
            with open(self.experiments_dir / experiment_id / 'experiment.json') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def run_batch_experiment(self, batch_id: str, output_formats: List[str], runs: int):
        """Run a batch experiment"""
        try:
            logger.info(f"Running batch experiment: {batch_id}")
            self.update_experiment(batch_id, {'status': 'RUNNING'})
            
            # Total sub experiments is the number of directories in the runs folder
            runs_path = self.experiments_dir / batch_id / 'runs'
            total_sub_experiments = len([d for d in runs_path.iterdir() if d.is_dir()])
            logger.info(f"Total sub experiments: {total_sub_experiments}")
            
            for run in range(total_sub_experiments):
                try:
                    self.run_batched_experiment(batch_id, str(run), output_formats, runs)
                except Exception as e:
                    logger.error(f"Error running sub experiment {run}: {e}")
                    raise e
                
            
        except Exception as e:
            logger.error(f"Error running batch experiment: {e}")
            self.update_experiment(batch_id, {'status': 'FAILED', 'error_message': str(e)})
        finally:
            pass



    def get_experiment_report(self, experiment_id):
        """Get experiment report"""
        report_dir = self.experiments_dir / experiment_id / 'report'
        for file in report_dir.glob('*.yaml'):
            with open(file) as f:
                return f.read()
        return None
    
    def run_experiment(self, experiment_id, output_formats, runs):
        """Run experiment"""
        if not self.acquire_lock():
            logger.info("Lock already held, skipping experiment check")
            return False
        try:
            logger.info(f"Changing experiment status to RUNNING")
            self.update_experiment(experiment_id, {'status': 'RUNNING'})
            experiment = self.get_experiment(experiment_id)['spec']
            report_path = self.experiments_dir / experiment_id / 'report'
            out_path = self.experiments_dir / experiment_id / 'data'

            orchestrator = KubernetesOrchestrator(experiment_config=experiment)
        
            engine = Engine(
                configuration_path=experiment,
                report_path=report_path,
                out_path=out_path,
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
                
                self.write_experiment_data(out_path, idx, experiment_id, responses, output_formats)

            # Write the report data to disk
            with open(report_path / "report.yaml", "w") as f:
                yaml.dump(report_data, f)
            logger.info(f"wrote report to {report_path / 'report.yaml'}")
        except Exception as e:
            logger.error(f"Error running experiment: {e}")
            import traceback
            logger.error(f"stacktrace: {traceback.format_exc()}")
            self.update_experiment(experiment_id, {'status': 'FAILED', 'error_message': str(e)})
        finally:
            self.update_experiment(experiment_id, {'status': 'COMPLETED'})
            self.release_lock()

    def run_batched_experiment(self,batch_id, sub_experiment_id, output_formats, runs):
        """Run batched experiment"""
        if not self.acquire_lock():
            logger.info("Lock already held, skipping experiment check")
            return False
        try:
            with open(self.experiments_dir / batch_id / 'runs' / sub_experiment_id / 'experiment.json') as f:
                experiment = json.load(f)
            report_path = self.experiments_dir / batch_id / 'runs' / sub_experiment_id / 'report'
            out_path = self.experiments_dir / batch_id / 'runs' / sub_experiment_id / 'data'

            orchestrator = KubernetesOrchestrator(experiment_config=experiment)
        
            engine = Engine(
                configuration_path=experiment,
                report_path=report_path,
                out_path=out_path,
                orchestrator_class=orchestrator,
                spec=experiment,
                id=sub_experiment_id
            )
            report_data = {}
            for idx in range(runs):
                responses, report_data = engine.run(orchestration_timeout=None, randomize=False, accounting=False)
                self.write_experiment_data(out_path, idx, sub_experiment_id, responses, output_formats)

            # Write the report data to disk
            with open(report_path / "report.yaml", "w") as f:
                yaml.dump(report_data, f)
            logger.info(f"wrote report to {report_path / 'report.yaml'}")
        except Exception as e:
            logger.error(f"Error running experiment: {e}")
            import traceback
            logger.error(f"stacktrace: {traceback.format_exc()}")
            raise e
        finally:
            self.release_lock()

    def experiment_exists(self, experiment_id):
        """Check if experiment exists"""
        return (self.experiments_dir / experiment_id / 'experiment.json').exists()


    def update_experiment(self, experiment_id, updates):
        """Update experiment config"""
        try:
            experiment = self.get_experiment(experiment_id)
            if experiment:
                experiment.update(updates)
                with open(self.experiments_dir / experiment_id / 'experiment.json', 'w') as f:
                    json.dump(experiment, f, indent=2)
                return experiment
            else:
                return None
        except Exception as e:
            logger.error(f"Error updating experiment: {e}")
            return None

    def list_experiments(self):
        """List all experiments"""
        experiments = {}
        for exp_dir in self.experiments_dir.iterdir():
            if exp_dir.is_dir():
                try:
                    with open(exp_dir / 'experiment.json') as f:
                        experiments[exp_dir.name] = json.load(f)
                except FileNotFoundError:
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
        '''gets experiments data for a given id and data format, the given file'''
        data_path = Path(self.experiments_dir) / experiment_id / 'data'
        
        # List all matching files for the given response name and file ending
        matching_files = list(data_path.glob(f"{run}_{experiment_id}_{response_name}.{file_ending}"))
        
        if not matching_files:
            raise FileNotFoundError(f"No {file_ending} files found for response {response_name}")
        
        # Match the file name to our convention
        path = data_path / f"{run}_{experiment_id}_{response_name}.{file_ending}"
        
        if file_ending == "json":
            return FileResponse(path, media_type="application/json", filename=f"{run}_{experiment_id}_{response_name}.{file_ending}")
        elif file_ending == "csv":
            return FileResponse(path, media_type="text/csv", filename=f"{run}_{experiment_id}_{response_name}.{file_ending}")
        else:
            logger.info("Unexpected file format requested")
            raise FileNotFoundError("Queried for an unsupported file format")

    def zip_experiment_data(self, experiment_id : str, path: Path):
        '''zips all the data for a given experiment id'''
        # Example zip file name: <experiment_id>.zip
        data_path = path / 'data'
        zip_path = path / f'{experiment_id}.zip'
        
        if not data_path.is_dir():
            logger.error(f"experiment directory for {experiment_id} does not exist")
            raise FileNotFoundError(f"experiment directory for {experiment_id} does not exist")
            
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=7) as zipf:
            for file in data_path.iterdir():
                if file.is_file():
                    zipf.write(file, arcname=file.name)
        logger.info(f"Zipped data for experiment: {experiment_id}")
        return zip_path
    
    def get_batched_experiment_id_by_params(self, batch_id: str, params: dict) -> Optional[str]:
        '''gets the experiment id for a given batch id and parameter combination'''
        param_df = pd.read_csv(self.experiments_dir / batch_id / 'params_to_id.csv')
        matching_row = param_df[(param_df == params).all(axis=1)]
        if not matching_row.empty:
            return matching_row.iloc[0]['sub_experiment_id']
        else:
            return None
    
    def get_batched_experiment_report(self, batch_id: str, sub_experiment_id: str) -> Optional[str]:
        '''gets the report for a given batch id and sub experiment id'''
        report_path = self.experiments_dir / batch_id / 'runs' / sub_experiment_id / 'report' / 'report.yaml'
        if not report_path.exists():
            return None
        with open(report_path, 'r') as f:
            return f.read()
        
        
    def get_batched_experiment_response_data(self, batch_id: str, sub_experiment_id: str, response_name: str, file_ending: str):
        '''gets the response data for a given batch id and sub experiment id'''
        data_path = self.experiments_dir / batch_id / 'runs' / sub_experiment_id / 'data'
        
        # List all matching files for the given response name and file ending
        matching_files = list(data_path.glob(f"{sub_experiment_id}_{batch_id}_{response_name}.{file_ending}"))
        
        if not matching_files:
            raise FileNotFoundError(f"No {file_ending} files found for response {response_name}")
        
        # Match the file name to our convention
        path = data_path / f"{sub_experiment_id}_{batch_id}_{response_name}.{file_ending}"
        
        if file_ending == "json":
            return FileResponse(path, media_type="application/json", filename=f"{sub_experiment_id}_{batch_id}_{response_name}.{file_ending}")
        elif file_ending == "csv":
            return FileResponse(path, media_type="text/csv", filename=f"{sub_experiment_id}_{batch_id}_{response_name}.{file_ending}")
        else:
            logger.info("Unexpected file format requested") 
            raise FileNotFoundError("Queried for an unsupported file format")
    
    def get_data(self, path: Path):
        '''gets all the data for a given path'''
        with open(path, 'rb') as file:
            yield from file

        
    def write_experiment_data(self, path: Path, run: int, experiment_id : str, responses : Dict[str, ResponseVariable], formats : List[str]):
        '''writes the response data to disk'''
        for _ , response in responses.items():
            for format in formats:
                if response.data is None:
                    logger.error(f"response data is None for {response.name}")
                    continue
                if format == "csv":
                    response.data.to_csv(path / f"{run}_{experiment_id}_{response.name}.csv", index=False)
                    logger.debug(f"wrote {run}_{experiment_id}_{response.name}.csv")
                elif format == "json":
                    if isinstance(response.data, pd.DataFrame):
                        response.data = response.data.to_dict(orient='records') # type: ignore
                   
                    with open(path / f"{run}_{experiment_id}_{response.name}.json", "w") as f:
                        json.dump(response.data, f)
                    logger.debug(f"wrote {run}_{experiment_id}_{response.name}.json")

    def list_experiment_variables(self, experiment_id : str )-> Optional[Tuple[List[str], List[str]]]:
        '''list all files (response varibales) in a given experiment folder, returns None if folder does not exist or is empty'''
        path = Path(self.experiments_dir ) / experiment_id / 'data'
        if not path.is_dir():
            logger.error(f"experiment directory {experiment_id} does not exist")
            return None
        
        # List all files in the data directory
        files = list(path.iterdir())
        if not files:
            logger.info(f"empty experiment directory with ID {experiment_id}, no reponse variables found")
            return None

        # Extract just the response variable name (after last underscore, before extension)
        variable_names = [file.name.split('_')[-1].split('.')[0] for file in files if file.is_file()]
        file_endings = [file.suffix[1:] for file in files if file.is_file()]

        if not variable_names:
            logger.info(f"empty experiment directory with ID {experiment_id}, no reponse variables found")
            return None

        return variable_names, file_endings
        
        


        

