"""
Purpose: Defines response variables for observing experiment results.
Functionality: Implements methods to query and process data from Prometheus and Jaeger.
Connection: Used by the Observer to collect and process response variables during experiments.

Implementations of Response Variables"""
import datetime

import numpy as np
import pandas as pd

from backend.internal.models.orchestrator import Orchestrator
from backend.internal.utils import humanize_utc_timestamp, time_string_to_seconds, to_milliseconds, to_microseconds
from backend.internal.errors import PrometheusException, JaegerException
from backend.internal.models.response import ResponseVariable
from backend.internal.jaeger import Jaeger
from backend.internal.prometheus import Prometheus
import logging

logger = logging.getLogger(__name__)


class MetricResponseVariable(ResponseVariable):
    @property
    def short_id(self) -> str:
        return self.id[:8]

    def __init__(
            self,
            orchestrator: Orchestrator,
            name: str,
            experiment_start: float,
            experiment_end: float,
            right_window: str,
            left_window: str,
            description: dict,
            target: str,
    ):
        super().__init__(
            experiment_start=experiment_start, experiment_end=experiment_end
        )
        self.orchestrator = orchestrator
        """Orchestrator interface to interact with docker or kubernetes"""
        self.name = name
        """User-defined name of the response variable"""
        self.metric_name = description["metric_name"]
        """User-supplied prometheus metric name"""
        self.description = description
        """Description of the response from the experiment spec"""
        self.labels = description.get("labels", {})
        """User-supplied prometheus label names and values"""
        self.step = description.get("step", 1)
        """User-supplied prometheus step size"""
        self.start = self.experiment_start - time_string_to_seconds(
            description["left_window"]
        )
        """Timestamp of the start of the observation period relative to experiment start"""
        self.end = self.experiment_end + time_string_to_seconds(
            description["right_window"]
        )
        self.right_window = right_window
        self.left_window = left_window
        """Timestamp of the end of the observation period relative to experiment end"""
        self.prometheus = Prometheus(orchestrator=self.orchestrator, target=target)
        """Prometheus API to fetch metric data represented by this response variable"""

    def __repr__(self):
        return (
            f"MetricResponse(name={self.name}, "
            f"start={self.humanized_start_timestamp}, "
            f"end={self.humanized_end_timestamp}, "
            f"step={self.step})"
        )

    @property
    def scaled_start_timestamp(self) -> float:
        """Scale the start timestamp to milliseconds"""
        return to_milliseconds(self.start)

    @property
    def scaled_end_timestamp(self) -> float:
        """Scale the end timestamp to milliseconds"""
        return to_milliseconds(self.end)

    @property
    def humanized_start_timestamp(self) -> datetime.datetime:
        """Return human-readable start timestamp"""
        return humanize_utc_timestamp(self.start)

    @property
    def humanized_end_timestamp(self) -> datetime.datetime:
        """Return human-readable end timestamp"""
        return humanize_utc_timestamp(self.end)

    def label(
            self,
            treatment_start: datetime.datetime,
            treatment_end: datetime.datetime,
            label_column: str,
            label: str,
    ) -> None:
        """Label a Prometheus dataframe. Note that Prometheus returns timestamps in seconds as a float"""
        if self.data is None or self.data.empty:
            self.data = pd.DataFrame(columns=['timestamp'])
            return
        
        # Convert UTC datetime to Prometheus timestamp
        prometheus_treatment_start = int(treatment_start.timestamp())
        prometheus_treatment_end = int(treatment_end.timestamp())
        
        predicate = self.data["timestamp"].between(prometheus_treatment_start, prometheus_treatment_end)
        self.data[label_column] = np.where(predicate, label, "NoTreatment")

    @staticmethod
    def _instant_query_to_df(json_data):
        """Returns a pandas dataframe from prometheus instant query json response"""
        results = json_data["data"]["result"]
        first = results[0]
        columns = list(first["metric"].keys())
        columns += ["timestamp", "metric_value"]
        ddict_list = []
        for result in results:
            ddict_list.append(
                {
                    **result["metric"],
                    "timestamp": result["value"][0],
                    "metric_value": result["value"][1],
                }
            )
        dataframe = pd.DataFrame(columns=columns, data=ddict_list)
        dataframe.set_index(pd.to_datetime(dataframe.timestamp, utc=True), inplace=True)
        return dataframe

    @staticmethod
    def _parse_metric_string(metric_value):
        try:
            return int(metric_value)
        except (TypeError, ValueError):
            try:
                return float(metric_value)
            except (TypeError, ValueError):
                return metric_value

    def _range_query_to_df(self, json_data, metric_column_name):
        """
        Return pandas dataframe from prometheus range query json response

        We index the dataframe by the supplied timestamp from Prometheus
        """
        try:
            results = json_data["data"]["result"]
            check = results[0]
            columns = list(check["metric"].keys())
            columns += ["timestamp", metric_column_name, self.name]
            rows = []
            for result in results:
                for timestamp, value in result["values"]:
                    parsed_value = self._parse_metric_string(value)
                    rows.append(
                        {
                            **result["metric"],
                            "timestamp": timestamp,
                            metric_column_name: parsed_value,
                            self.name: parsed_value,
                        }
                    )
            dataframe = pd.DataFrame(columns=columns, data=rows)
            dataframe.set_index(
                pd.to_datetime(dataframe.timestamp, utc=True, unit="s"), inplace=True
            )
            return dataframe
        except (IndexError, KeyError) as exc:
            raise PrometheusException(
                message="Cannot create dataframe from empty Prometheus response",
                explanation=f"{exc}",
            )

    def observe(self):
        try:
            prometheus_query = self.prometheus.build_query(
                metric_name=self.metric_name,
                label_dict=self.labels,
            )
            prometheus_metrics = self.prometheus.range_query(
                query=prometheus_query,
                start=self.start,
                end=self.end,
                step=self.step,
            )
            self.data = self._range_query_to_df(
                prometheus_metrics, metric_column_name=self.metric_name
            )
            return self.data
        except PrometheusException as e:
            # Initialize with empty DataFrame instead of None
            self.data = pd.DataFrame(columns=['timestamp'])
            raise e


class TraceResponseVariable(ResponseVariable):
    def __init__(
            self,
            orchestrator: Orchestrator,
            name: str,
            experiment_start: float,
            experiment_end: float,
            right_window: str,
            left_window: str,
            description: dict,
    ):
        super(TraceResponseVariable, self).__init__(
            experiment_start=experiment_start,
            experiment_end=experiment_end,
        )
        self.orchestrator = orchestrator
        """Orchestrator interface to interact with docker or kubernetes"""
        self.name = name
        """User-defined name of the response variable"""
        self.service_name = description["service_name"]
        """Service name to search traces in Jaeger"""
        self.limit = description.get("limit", 100)
        """Limit number of traces when searching with Jaeger"""
        self.start = self.experiment_start - time_string_to_seconds(
            description["left_window"]
        )
        """UTC Timestamp of the start of the observation period relative to the experiment start"""
        self.end = self.experiment_end + time_string_to_seconds(
            description["right_window"]
        )
        self.right_window = right_window
        self.left_window = left_window
        """UTC Timestamp of the end of the observation period relative to the experiment end"""
        self.jaeger = Jaeger(orchestrator=self.orchestrator)
        """Jaeger API to observe trace data"""

    def __repr__(self):
        return (
            f"TraceResponse(name={self.name}, start={self.humanized_start_timestamp}, "
            f"end={self.humanized_end_timestamp}, service={self.service_name})"
        )

    @property
    def short_id(self) -> str:
        """Truncated id"""
        return self.id[:8]

    @property
    def scaled_start_timestamp(self):
        """Scale the start timestamp to microseconds"""
        return to_microseconds(self.start)

    @property
    def scaled_end_timestamp(self):
        """Scale the end timestamp to microseconds"""
        return to_microseconds(self.end)

    @property
    def humanized_start_timestamp(self):
        """Return human-readable start timestamp"""
        return humanize_utc_timestamp(self.start)

    @property
    def humanized_end_timestamp(self):
        """Return human-readable end timestamp"""
        return humanize_utc_timestamp(self.end)

    @property
    def _jaeger_start_timestamp(self):
        """Return a timestamp version Jaeger accepts"""
        return int(self.scaled_start_timestamp)

    @property
    def _jaeger_end_timestamp(self):
        """Return an end timestamp Jaeger accepts"""
        return int(self.scaled_end_timestamp)

    def label(
            self,
            treatment_start: datetime.datetime,
            treatment_end: datetime.datetime,
            label_column: str,
            label: str,
    ) -> None:
        """Label a dataframe containing Jaeger spans depending on the span start timestamp"""
        if self.data is None or self.data.empty:
            # TODO handle this better
            self.data = pd.DataFrame(columns=['start_time'])
            return
        
        # Convert UTC datetime to Jaeger microsecond timestamp
        jaeger_treatment_start = int(treatment_start.timestamp() * 1_000_000)
        jaeger_treatment_end = int(treatment_end.timestamp() * 1_000_000)

        # Debug prints
        logger.info(f"\nTimestamp comparisons:")
        logger.info(f"Treatment start (UTC): {treatment_start}")
        logger.info(f"Treatment start (Jaeger μs): {jaeger_treatment_start}")
        logger.info(f"Treatment end (UTC): {treatment_end}")
        logger.info(f"Treatment end (Jaeger μs): {jaeger_treatment_end}")
        
        if not self.data.empty:
            logger.info(f"\nSample data timestamps:")
            logger.info(f"First row start_time: {self.data['start_time'].iloc[0]}")
            logger.info(f"Last row start_time: {self.data['start_time'].iloc[-1]}")

        predicate = (self.data["start_time"] >= jaeger_treatment_start) & (
                self.data["start_time"] <= jaeger_treatment_end
        )
        
        # Print predicate results
        if not self.data.empty:
            logger.info(f"\nPredicate matches: {predicate.sum()} out of {len(predicate)} rows")
        
        self.data[label_column] = np.where(predicate, label, "NoTreatment")

    @staticmethod
    def _tabulate(trace_json) -> pd.DataFrame:
        """
        Transform Jaeger traces to a tabular structure.
        We additionally index the resulting dataframe with
        utc-aware datetime index based on the start time of spans.
        """
        # TODO: include tag information
        # TODO: this function is too long. split up into smaller functions
        # for the difference between parent and follow references confer
        # https://github.com/opentracing/specification/blob/master/specification.md#references-between-spans
        # CHILD_OF indicates that the parent span depends on the child span
        # FOLLOWS_FROM indicates that the parent span does not depend on the child span, but is causally related
        # distribute these relationships as a separate causality dataframe
        columns = [
            "trace_id",
            "span_id",
            "operation",
            "start_time",
            "end_time",
            "duration",
            "service_name",
            "span_kind",
            "req_status_code",
            "ref_type",
            "ref_type_span_ID",
            "ref_type_trace_ID"
        ]
        dataframes = []

        for trace in trace_json["data"]:
            spans = trace["spans"]
            processes = trace["processes"]
            trace_rows = []
            for span in spans:
                trace_id = span["traceID"]
                span_id = span["spanID"]
                operation = span["operationName"]
                start = span["startTime"]
                duration = span["duration"]
                end = start + duration
                process_id = span["processID"]
                process_dict = processes.get(process_id)
                service_name = process_dict["serviceName"]

                # adding the span kind : internal / client / service / consumer / producer
                # adding the status code of rRPC / http request or -1 if spankind == interna
                req_status_code = "N/A"
                span_kind = "N/A"
                if "tags" in span and isinstance(span["tags"], list):
                    for obj in span["tags"]:
                        if obj["key"] == "span.kind":
                            span_kind = obj["value"]
                        if obj["key"] == "rpc.grpc.status_code":
                            req_status_code = obj["value"]
                            # here add http status code option
                            # since the application talks in gRPC and the Frontend and Frontend Proxy with with HTTP
                        if obj["key"] == "http.status_code":
                            req_status_code = obj["value"]
                ref_type = "N/A"
                ref_type_spanID = "N/A"
                ref_type_traceID = "N/A"
                if span["references"]:
                    ref_type = span["references"][0]["refType"]
                    ref_type_spanID = span["references"][0]["spanID"]
                    ref_type_traceID = span["references"][0]["traceID"]
                # adding the reftype per span "CHILD_of" / "follows_from"
                # adding the spankind span ID and the spankind trace
                row = [trace_id, span_id, operation, start, end, duration, service_name, span_kind, req_status_code, ref_type, ref_type_spanID, ref_type_traceID]
                trace_rows.append(row)
            dataframe = pd.DataFrame(trace_rows, columns=columns)
            dataframe["duration"] = pd.to_numeric(dataframe["duration"])
            dataframe.reset_index(inplace=True)
            dataframe.set_index(
                pd.to_datetime(dataframe.start_time, utc=True, unit="us"), inplace=True
            )
            dataframes.append(dataframe)
        try:
            merged = pd.concat(dataframes)
        except ValueError:
            raise JaegerException(
                message="Cannot concatenate dataframes",
                explanation="Jaeger sent an empty response",
            )
        return merged

    def observe(self) -> pd.DataFrame:
        """Observe the data service represented by this response variable"""
        try:
            traces = self.jaeger.search_traces(
                service_name=self.service_name,
                start=self._jaeger_start_timestamp,
                end=self._jaeger_end_timestamp,
                limit=self.limit,
            )
            trace_df = self._tabulate(trace_json=traces)
            self.data = trace_df
            return trace_df
        except JaegerException as e:
            # TODO handle this better
            self.data = pd.DataFrame(columns=['start_time'])
            raise e
