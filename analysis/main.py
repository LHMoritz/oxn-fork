from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from internal.AnalysisManager import AnalysisManager
from internal.utils import load_model
from internal.StorageClient import LocalStorageHandler
from pydantic import BaseModel
from typing import Optional, List
from internal.exceptions import OXNFileNotFound, NoDataForExperiment, ConfigFileNotFound, LabelNotPresent

app = FastAPI(title="Analysis API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000"],  # Backend URL, and Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


VOLUME_MOUNT = "/mnt/oxn-data"
ANALYIS_MOUNT = "/mnt/analysis-datastore"
trace_model = load_model()
storage_handler = LocalStorageHandler(VOLUME_MOUNT)

# data validation

class Message(BaseModel):
    message : str

class VariableMetrics(BaseModel):
    micro_precision: float
    micro_recall : float
    micro_f1_score : float

class Conditional_Prob(BaseModel):
    good_Error : Optional[float]
    good_No_Error : Optional[float]
    faulty_Error : Optional[float]
    faulty_No_Error : Optional[float]

class TimeToResults(BaseModel):
    pass

class DataLength(BaseModel):
    pass

class AnalysisResponse(BaseModel):
    experiment_id : str
    metrics : List[VariableMetrics]
    probability : List[Conditional_Prob]
    message : Message
    dataLenght : DataLength
    timeToResults : TimeToResults


ERROR_MESSAGES = {
    FileNotFoundError: "Error Accessing the Database: {}",
    OXNFileNotFound: "Could not find experiment in the Database: {}",
    NoDataForExperiment: "No Data present for experiment: {}",
    ConfigFileNotFound: "Could not find Configuration for experiment: {}",
    LabelNotPresent: "Could not find label for supervised learning in config file: {}",
}

def construct_message(e: Exception) -> str:
    for exception_type, message in ERROR_MESSAGES.items():
        if isinstance(e, exception_type):
            return message.format(str(e))
    return f"An error occurred: {str(e)}"


@app.get("/analyze", response_model=AnalysisResponse)
def analyze_experiment(experiment_id : str):

    response_massage : str = None
    metric_dict : str = None
    prob_dict : str = None

    try:

        analysis_manager = AnalysisManager(experiment_id=experiment_id, local_storage_handler=storage_handler, trace_model=trace_model)
        metric_dict , prob_dict = analysis_manager.analyze_experimment()

    except Exception as e:
        response_massage = construct_message(e)
    
    response = {
        "experiment_id" : experiment_id,
        "metrics" : metric_dict if  metric_dict is not None else [],
        "probability" : prob_dict if prob_dict is not None else [],
        "message" : response_massage
    }

    return response


@app.get("/health")
def health_check():
    return {"Hello": "Healty sign from Analysis :)"}
