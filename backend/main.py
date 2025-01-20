from pathlib import Path
from gevent import monkey

from backend.internal.errors import StoreException
monkey.patch_all()

from typing import Dict, List, Optional, Union
import logging

""" uvicorn_logger_error = logging.getLogger("uvicorn.error")
uvicorn_logger_error.setLevel(logging.DEBUG)
uvicorn_logger_access = logging.getLogger("uvicorn.access")
uvicorn_logger_access.setLevel(logging.DEBUG)

logger = logging.getLogger("uvicorn")   
 """
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

data_dir = "data"
report_dir = "report"
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from datetime import datetime
from backend.internal.experiment_manager import ExperimentManager
from fastapi.responses import FileResponse, StreamingResponse
from backend.internal.store import LocalFSStore



app = FastAPI(title="OXN API", version="1.0.0")

############### CORS Middleware ###############
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Alle HTTP-Methoden erlauben
    allow_headers=["*"],  # Alle Headers erlauben
)

""" @app.on_event("startup")
async def startup_event():
    logger = logging.getLogger("uvicorn.access")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler) """

############### Store and Experiment Manager ###############
base_path = "/mnt/oxn-data"
store = LocalFSStore(base_path)
experiment_manager = ExperimentManager(Path(base_path), store)
experiments_dir = Path(base_path) / 'experiments'

############### Pydantic models for request/response validation ###############
class ExperimentCreate(BaseModel):
    name: str
    config: Dict
class BatchExperimentCreate(BaseModel):
    name: str
    config: Dict
    parameter_variations: Dict[str, List[Union[str, float]]] 
class ExperimentRun(BaseModel):
    runs: int = 1
    output_formats: List[str] = ["json"]  # or csv

class ExperimentStatus(BaseModel):
    id: str
    name: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


@app.post("/experiments", response_model=ExperimentStatus)
async def create_experiment(experiment: ExperimentCreate):
    """
    Create a new experiment with configuration.
    Stores experiment metadata and creates necessary directories.
    """
    logger.info(f"API: Creating experiment: {experiment.name}")
    return experiment_manager.create_experiment(
        name=experiment.name,
        config=experiment.config
    )

@app.post("/experiments/{experiment_id}/run", response_model=Dict)
async def run_experiment(
    experiment_id: str,
    run_config: ExperimentRun,
    background_tasks: BackgroundTasks
):
    """
    Start experiment execution asynchronously.
    - Validates experiment exists
    - Checks if another experiment is running
    - Starts execution in background
    - Returns immediately with acceptance status
    """
    if not experiment_manager.get_experiment_config(experiment_id):
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    logger.info(f"Adding background task for experiment: {experiment_id}")
    background_tasks.add_task(
        experiment_manager.run_experiment,
        experiment_id,
        output_formats=run_config.output_formats,
        runs=run_config.runs
    )
    
    return {
        "status": "accepted",
        "message": "Experiment started successfully",
        "experiment_id": experiment_id
    }

@app.post("/experiments/{experiment_id}/runsync", response_model=Dict)
async def run_experiment_sync(
    experiment_id: str,
    run_config: ExperimentRun,
):
    """
    Start experiment execution asynchronously.
    - Validates experiment exists
    - Checks if another experiment is running
    - Starts execution in background
    - Returns immediately with acceptance status
    """
    if not experiment_manager.get_experiment_config(experiment_id):
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    
    logger.info(f"Running experiment synchronously: {experiment_id}")
    experiment_manager.run_experiment(
        experiment_id,
        output_formats=run_config.output_formats,
        runs=run_config.runs
    )
    
    return {
        "status": "accepted",
        "message": "Experiment started successfully",
        "experiment_id": experiment_id
    }

@app.get("/experiments/{experiment_id}/data")
async def get_experiment_data(experiment_id: str):
    """Get experiment data as zip file"""
    memory_zip = experiment_manager.get_experiment_data(experiment_id)
    return Response(
        content=memory_zip.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={experiment_id}.zip"}
    )

@app.get("/experiments/{experiment_id}/status", response_model=ExperimentStatus)
async def get_experiment_status(experiment_id: str):
    """Get current status of an experiment"""
    experiment = experiment_manager.get_experiment_config(experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    response = ExperimentStatus(
        id=experiment_id,
        name=experiment["name"],
        status=experiment["status"],
        started_at=experiment["started_at"],
        completed_at=experiment["completed_at"],
        error_message=experiment["error_message"]
    )
    return response

""" '''gets the resulting data for the given experiment id and respone variable id and the file format. If file is found it will be returned. Else a 404 not found will be given.
Supported file types are json and csv. '''
@app.get("/experiments/{experiment_id}/data/{response_name}/", response_class=None)
async def get_experiment_data(
    experiment_id: str,
    response_name : str,
    format: str = Query("csv", regex="^(json|csv)$")
):
    if format not in {"json", "csv"}:
        raise HTTPException(status_code=400, detail="Invalid type. Only 'json' and 'csv' are allowed.")
    try:
        return experiment_manager.get_experiment_data(experiment_id=experiment_id, response_name=response_name, file_ending=format)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"response variable: {response_name} for experiment: {experiment_id} not found")
   
'''Lists the reponse variables in the directory for a given, experiment id with file ending suffixes. Gives back empty lists if experiemnt id is not
a directory, or the directory is emtpy. Will be mainly used by the analysis service'''
@app.get("/experiments/{experiment_id}" , response_model=None)
async def list_experiment_files(
    experiment_id : str
):
    res  =  experiment_manager.list_experiment_variables(experiment_id=experiment_id)
    if res is not None:
        return {"response_names": res[0], "response_file_suffixes": res[1]}
    else:
        return {"response_names": [], "response_file_suffixes": []} """

@app.get("/experiments/{experiment_id}/benchmark")
async def get_benchmark_data(experiment_id: str):
    """
    Get benchmark results for experiment.
    Returns CSV file with detection times and accuracy metrics.
    """
    # TODO: Implement CSV file download response
    pass

@app.get("/experiments/{experiment_id}/report")
async def get_experiment_report(experiment_id: str):
    """
    Get experiment report for experiment.
    Returns HTML file with experiment results.
    """
    report = experiment_manager.get_experiment_report(experiment_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

# Additional Feature Endpoints
@app.post("/experiments/batch")
async def create_batch_experiment(batch_experiment: BatchExperimentCreate):
    logger.info(f"API: Creating batch experiment: {batch_experiment.name}")
    return experiment_manager.create_batch_experiment(batch_experiment.name, batch_experiment.config, batch_experiment.parameter_variations)

@app.post("/experiments/batch/{batch_id}/run")
async def run_batch_experiment(batch_id: str, experiment_config: ExperimentRun):
    return experiment_manager.run_batch_experiment(batch_id, experiment_config.output_formats, experiment_config.runs)


@app.get("/experiments/batch/{batch_id}/{sub_experiment_id}/report")
async def get_batch_experiment_report(batch_id: str, sub_experiment_id: str):
    report = experiment_manager.get_batched_experiment_report(batch_id, sub_experiment_id)

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@app.get("/experiments/batch/{batch_id}/{sub_experiment_id}/data")
async def get_batch_experiment_data(batch_id: str, sub_experiment_id: str):
    """
    Get batch experiment data of a given sub experiment id
    """
    logger.debug(f"Getting data for batch experiment: {sub_experiment_id}")
    key = f"{batch_id}_{sub_experiment_id}"
    zip_file = experiment_manager.get_experiment_data(key)
    
    logger.debug(f"Returning zip file for batch experiment: {sub_experiment_id}")
    return Response(
        content=zip_file.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={sub_experiment_id}.zip"}
    )

@app.get("/experiments/batch/{batch_id}/sub_experiment_id")
async def get_batch_experiment_id(
    batch_id: str,
    request: Request
):
    """
    Get the sub experiment id for a given batch id and parameter combination
    
    Query params should be provided as key-value pairs, e.g. ?param1=value1&param2=value2
    """
    params = request.query_params
    if not params:
        raise HTTPException(status_code=400, detail="Parameter query values are required")
    logger.debug(f"params: {params}")
    try:
        param_dict = dict(params)
        return experiment_manager.get_batched_experiment_id_by_params(batch_id, param_dict)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StoreException as e:
        raise HTTPException(status_code=500, detail=str(e))

'''This endpoint lists all experiments in the file system with corresponding meta data. The difference  to the route : /experiemnts/experiments_id that this route lists
repsonse variables inside a directory and does not list directories. This route will be mainly used by the frontend.'''
@app.get("/experiments", response_model=List[ExperimentStatus])
async def list_experiments(
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100)
):
    """
    List all experiments
    """
    experiments = experiment_manager.list_experiments()
    response = []
    for e in experiments:
        response.append(ExperimentStatus(
            id=experiments[e]["id"],
            name=experiments[e]["name"],
            status=experiments[e]["status"],
            started_at=experiments[e]["started_at"],
            completed_at=experiments[e]["completed_at"],
            error_message=experiments[e]["error_message"]
        ))
    return response


@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

@app.get("/experiments/{experiment_id}/config")
async def get_experiment_config(experiment_id: str):
    """Get experiment configuration"""
    return experiment_manager.get_experiment_config(experiment_id)

# run with uvicorn:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_config=None)
