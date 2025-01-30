export const resultsMockData = [
  {
    "experiment_id": "01733873826",
    "date": "2024-12-10T13:21:02.143Z",
    "runs": {
      "run_1": {
        "date": "2024-12-10T13:21:02.143Z",
        "id": "1",
        "interactions": {
          "interaction_0": {
            "treatment_name": "empty_treatment",
            "treatment_type": "EmptyTreatment",
            "treatment_start": "2024-12-10T13:21:02.143Z",
            "treatment_end": "2024-12-10T13:48:42.143Z",
            "response_name": "frontend_traces.duration",
            "response_start": "2024-11-17T15:10:36.141Z",
            "response_end": "2024-11-17T15:16:06.144Z",
            "response_type": "TraceResponseVariable",
            "store_key": "/tmp/latest.yml/6213b211/frontend_traces"
          },
          "interaction_1": {
            "treatment_name": "sample1_treatment",
            "treatment_type": "Sample1Treatment",
            "treatment_start": "2024-12-10T13:22:10.143Z",
            "treatment_end": "2024-12-10T13:51:36.143Z",
            "response_name": "frontend_traces.duration",
            "response_start": "2024-11-17T15:10:36.141Z",
            "response_end": "2024-11-17T15:16:06.144Z",
            "response_type": "TraceResponseVariable",
            "store_key": "/tmp/latest.yml/6213b211/frontend_traces"
          }
        },
        "loadgen": {
          "loadgen_start_time": "2024-11-17T15:10:46.141Z",
          "loadgen_end_time": "2024-11-17T15:16:07.459Z",
          "loadgen_total_requests": 39533,
          "loadgen_total_failures": 103
        }
      },
    }
  },
]

export const resultsMockData2 = [
  {
    experimentDate: "2020-10-10",
    experimentId: "1",
    numberOfRuns: 2,
    treatmentNames: ["treatment1", "treatment2"],
    treatmentTypes: ["type1", "type2"],
  }
]