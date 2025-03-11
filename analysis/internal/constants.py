
"""
This file just contains conmstants I use throught the entire backend
"""

from pathlib import Path

SERVICE_NAME_COLUMN = "service_name"
SPAN_ID_COLUMN = "span_id"
REF_TYPE_SPAN_ID = "ref_type_span_ID"
DURATION_COLUMN = "duration"
TRACE_ID_COLUMN = "trace_id"
START_TIME = 'start_time'
SPAN_KIND = 'span_kind'
NOT_AVAILABLE = "N/A"

REQUIRED_COLUMNS = ["trace_id","span_id", "operation" , "start_time", "end_time", "duration", "service_name" ,"span_kind",
                     "req_status_code", "ref_type", "ref_type_span_ID", "ref_type_trace_ID", "add_security_context" ]


NO_TREATMENT = "NoTreatment"
PROJECT_ID = "advanced-cloud-prototyping"

ADJENCY_TOTAL_PRE = "adjency_total_csv_"

INTERNAL_TYPE = "internal"
REQ_STATUS_CODE = "req_status_code"
ERROR_IN_TRACE_COLUMN = "has_error_in_trace"


# for the error ratio dictionary
FAULTY_ERROR = "faultyError"
FAULTY_NO_ERROR = "faultyNoError"
GOOD_ERROR = "goodError"
GOOD_NO_ERROR = "goodNoError"


'''
To build the adjency matrix and construct input vectors for the MLP classifier we need need a constant mapping so each vector has the same structure.
This list comes from the opentelemetry-demo source code wihtin this repository and should be updated if the demo changes or another version is taken.
The Integers as corresponding values will be the corresponding index values to build the Adj. Matrix

I will omit the following Microservices that are in the arcitecture but do not really yield traces:

    - ffpostgres
    - kafka
    - grafana

'''
SERVICES = {
    "frontendproxy": 0,
    "frontend": 1,
    "featureflagservice": 2,
    "accountingservice": 3,
    "adservice": 4,
    "checkoutservice": 5,
    "currencyservice": 6,
    "emailservice": 7,
    "frauddetectionservice": 8,
    "paymentservice": 9,
    "productcatalogservice": 10,
    "quoteservice": 11,
    "recommendationservice": 12,
    "shippingservice": 13,
    "cartservice": 14,
    "flagd": 15
}

SERVICES_REVERSE = {
    0: "frontendproxy",
    1: "frontend",
    2: "featureflagservice",
    3: "accountingservice",
    4: "adservice",
    5: "checkoutservice",
    6: "currencyservice",
    7: "emailservice",
    8: "frauddetectionservice",
    9: "paymentservice",
    10: "productcatalogservice",
    11: "quoteservice",
    12: "recommendationservice",
    13: "shippingservice",
    14: "cartservice",
    15 : "flagd"
}

# machine learning model constants
MODEL_DIMENSIONS = [257, 1500, 1500, 1500, 17]
SMALL_MODEL_DIMENSIONS = [257, 1500, 17]
MODEL_DIMENSIONS_BINARY = [257, 1500, 2]
#ODEL_PATH = "./model/new_traceModel.pt"
METRICS = ["micro_precision", "micro_recall", "micro_f1_score"]
MODEL_PATH = Path("internal/model") / "real_tracemodel.pt"

MODEL_PATH_BIG_MODEL = Path("internal/model") / "real_tracemodel_big.pt"


