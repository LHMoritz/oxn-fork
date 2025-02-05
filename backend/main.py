from pathlib import Path
from gevent import monkey
import os
import json

from backend.internal.errors import StoreException
from backend.internal.models.fault_detection import FaultDetectionAnalysisResponse
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
from backend.internal.models.experiment import CreateBatchExperimentRequest, CreateBatchExperimentResponse, CreateExperimentResponse, Experiment, ExperimentStatus, RunExperimentRequest


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
base_path = os.getenv("OXN_RESULTS_PATH", "/mnt/oxn-data")
store = LocalFSStore(base_path)
experiment_manager = ExperimentManager(Path(base_path), store)
experiments_dir = Path(base_path) / 'experiments'

############### Pydantic models for request/response validation ###############


@app.post("/experiments", response_model=CreateExperimentResponse)
async def create_experiment(experiment: Experiment):
    """
    Create a new experiment with configuration.
    Stores experiment metadata and creates necessary directories.
    """
    logger.info(f"API: Creating experiment: {experiment.name}")
    return experiment_manager.create_experiment(
        name=experiment.name,
        config=experiment
    )

# WIP - Execution not guaranteed to be started
@app.post("/experiments/{experiment_id}/run", response_model=Dict)
async def run_experiment(
    experiment_id: str,
    run_config: RunExperimentRequest,
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

@app.post("/experiments/{experiment_id}/runsync", response_model=Experiment)
async def run_experiment_sync(
    experiment_id: str,
    run_config: RunExperimentRequest,
):
    """
    Start experiment execution asynchronously.
    - Validates experiment exists
    - Checks if another experiment is running
    """
    if not experiment_manager.get_experiment_config(experiment_id):
        raise HTTPException(status_code=404, detail="Experiment not found")
        
    logger.info(f"Running experiment synchronously: {experiment_id}")
    try:
        experiment_manager.run_experiment(
            experiment_id,
            output_formats=run_config.output_formats,
            runs=run_config.runs
        )
    except Exception as e:
        experiment_manager.update_experiment_config(experiment_id, {'status': 'FAILED', 'error_message': str(e)})
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "status": "accepted",
        "message": "Experiment completed successfully",
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
    status = experiment_manager.get_experiment_status(experiment_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return status

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

@app.post("/experiments/batch", response_model=CreateBatchExperimentResponse)
async def create_batch_experiment(batch_experiment: CreateBatchExperimentRequest):
    logger.info(f"API: Creating batch experiment: {batch_experiment.name}")
    return experiment_manager.create_batch_experiment(batch_experiment.name, batch_experiment.config, batch_experiment.parameter_variations)

@app.post("/experiments/batch/{batch_id}/run")
async def run_batch_experiment(batch_id: str, experiment_config: RunExperimentRequest, analyze: bool = Query(False, description="Enable analysis after experiment completion")):
    try:
        return experiment_manager.run_batch_experiment(batch_id, experiment_config.output_formats, experiment_config.runs, analyze)
    except Exception as e:
        logger.error(f"Error running batch experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/experiments", response_model=List[ExperimentStatus])
async def list_experiments(
    status: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100)
):
    """
    List all experiments
    """
    return experiment_manager.list_experiments_status(status_filter=status, limit=limit)
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

@app.get("/experiments/{experiment_id}/config")
async def get_experiment_config(experiment_id: str):
    """Get experiment configuration"""
    return experiment_manager.get_experiment_config(experiment_id)

@app.get("/experiments/{experiment_id}/analyse-fault-detection", response_model=List[FaultDetectionAnalysisResponse])
async def analyse_fault_detection(experiment_id: str):
    """Analyse fault detection for an experiment"""
    try:
        results = experiment_manager.analyze_fault_detection(experiment_id)
    except ValueError as e:
        logger.error(f"Error analysing fault detection for experiment {experiment_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error analysing fault detection for experiment {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    response = []
    for result in results:
        response.append(FaultDetectionAnalysisResponse(
            fault_name=result.fault_name,
            detected=result.detected,
            detection_time=result.detection_time,
            detection_latency=result.detection_latency,
            true_positives=result.true_positives,
            false_positives=result.false_positives
        ))
    return response

@app.get("/experiments/{experiment_id}/raw-detections")
async def get_experiment_detections(experiment_id: str):
    """Get raw detection data for an experiment"""
    return experiment_manager.get_experiment_detections(experiment_id)

# run with uvicorn:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_config=None)
