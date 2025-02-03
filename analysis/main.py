from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from analysis.internal.AnalysisManager import AnalysisManager
from analysis.internal.utils import load_model
from analysis.internal.StorageClient import LocalStorageHandler
import logging
import os
app = FastAPI(title="Analysis API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000"],  # Backend URL, and Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# mount paths to the K8s persistent volumes
VOLUME_MOUNT = os.getenv("OXN_RESULTS_PATH", "/mnt/oxn-data")
ANALYIS_MOUNT = os.getenv("OXN_ANALYSIS_PATH", "/mnt/analysis-datastore")

# "Singleton classes"
trace_model = load_model()
storage_handler = LocalStorageHandler(VOLUME_MOUNT, 'experiments' , ANALYIS_MOUNT)


def analysis_background_task(experiment_id : str): 
    try:
        logger.info(f"starting experiment with id {experiment_id}")
        analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
        analysis_manager.analyze_experiment()
    except Exception as e:
        logger.error(f"An error occured: {str(e)}")
        

@app.get("/analyze")
def analyze_experiment(experiment_id : str, background_task : BackgroundTasks):

    background_task.add_task(analysis_background_task, experiment_id)
    return {"message" : f"processing analysis for experiment_id: {experiment_id}"}
    
@app.get("/health")
def health_check():
    return {"Hello": "Healty sign from Analysis :)"}
