"""
Purpose: Manages the execution of an experiment run.
Functionality: Applies treatments, runs the experiment, and collects results.
Connection: Core component that uses treatments and observer to perform an experiment.

Experiment runner"""
import logging
import random
import time
import uuid
import hashlib
import datetime
from typing import List
from dataclasses import dataclass
import psutil

import docker

from backend.internal.errors import OxnException, PrometheusException, JaegerException
from backend.internal.models.experiment import Experiment
from backend.internal.treatments import (
    DeploymentScaleTreatment,
    EmptyDockerComposeTreatment,
    EmptyKubernetesTreatment,
    EmptyTreatment,
    KubernetesApplySecurityContextTreatment,
    KubernetesKillTreatment,
    KubernetesMetricsExportIntervalTreatment,
    KubernetesNetworkDelayTreatment,
    KubernetesNetworkPacketLossTreatment,
    KubernetesPrometheusIntervalTreatment,
    KubernetesPrometheusRulesTreatment,
    PauseTreatment,
    PacketLossTreatment,
    PrometheusIntervalTreatment,
    StressTreatment,
    TailSamplingTreatment,
    KillTreatment,
    MetricsExportIntervalTreatment,
    ProbabilisticSamplingTreatment,
    KubernetesProbabilisticHeadSamplingTreatment
)
from backend.internal.utils import utc_timestamp, humanize_utc_timestamp
from backend.internal.observer import Observer
from backend.internal.pricing import Accountant
from backend.internal.models.treatment import Treatment
from backend.internal.models.orchestrator import Orchestrator
logger = logging.getLogger(__name__)

@dataclass
class TreatmentData:
    name: str
    start: datetime.datetime | None
    end: datetime.datetime | None


class ExperimentRunner:
    """
    Class that represents execution of experiments

    From the perspective of the runner, it always executes only a single run of an experiment.
    Multiple runs, asynchronous runs should be handled outside the runner.
    The runner builds the treatments, executes them in the provided order from the spec, observes the responses
    and then labels the resulting data with treatment information.
    The runner additionally waits for the specified time intervals depending on experiment configuration.

    """
    # TODO: make names less ambiguous
    treatment_keys = {
        "kill": KillTreatment,
        "pause": PauseTreatment,
        "loss": PacketLossTreatment,
        "kubernetes_loss": KubernetesNetworkPacketLossTreatment,
        "empty": EmptyTreatment,
        "empty_kubernetes": EmptyKubernetesTreatment,
        "empty_docker_compose": EmptyDockerComposeTreatment,
        "delay": KubernetesNetworkDelayTreatment,
        "stress": StressTreatment,
        "sampling": PrometheusIntervalTreatment,
        "kubernetes_prometheus_interval": KubernetesPrometheusIntervalTreatment,
        "kubernetes_prometheus_rules": KubernetesPrometheusRulesTreatment,
        "tail": TailSamplingTreatment,
        "probl": ProbabilisticSamplingTreatment,
        "kube_probl": KubernetesProbabilisticHeadSamplingTreatment,
        "otel_metrics_interval": MetricsExportIntervalTreatment,
        "kubernetes_otel_metrics_interval": KubernetesMetricsExportIntervalTreatment,
        "scale_deployment": DeploymentScaleTreatment,
        "security_context_kubernetes": KubernetesApplySecurityContextTreatment,
        "kubernetes_kill": KubernetesKillTreatment,
        
    }

    def __init__(
            self,
            orchestrator:Orchestrator,
            config: Experiment,
            experiment_id=None,
            additional_treatments=None,
            random_treatment_order=False,
            accountant_names=None,
    ):
        self.orchestrator = orchestrator
        self.config = config
        """Experiment specification dict"""
        self.experiment_id = experiment_id
        """Experiment specification filename"""
        self.id = uuid.uuid4().hex
        """Random and unique ID to identify runs"""
        self.treatments = {}  # since python 3.6 dict remembers order of insertion
        self.typed_treatments: List[TreatmentData] = []
        """Treatments to execute for this run"""
        self.experiment_start = None
        """Experiment start as UTC unix timestamp in seconds"""
        self.experiment_end = None
        """Experiment end as UTC unix timestamp in seconds"""
        self.random_treatment_order = random_treatment_order
        """If the treatments should be executed in random order"""
        self.additional_treatments = (
            additional_treatments if additional_treatments else []
        )
        """Additional user-supplied treatments"""
        self.observer = Observer(orchestrator=self.orchestrator, config=self.config)
        """Observer for response variables"""
        self.accountant = None
        if accountant_names:
            self.accountant = Accountant(
                client=docker.from_env(),
                container_names=accountant_names,
                process=psutil.Process(),
            )
        """Accountant to determine resource expenditure during experiments"""
        self._compute_hash()
        """Compute unique identifiers for runs and experiment config"""
        self._extend_treatments()
        """Populate the treatment_keys class variable with additional user-supplied treatments"""
        self._build_treatments()
        """Populate the treatment dicts from the config and any user-supplied treatments"""

    def __repr__(self):
        return f"ExperimentRunner(config={self.experiment_id}, hash={self.short_hash}, run={self.short_id})"

    @property
    def short_id(self) -> str:
        """Return the truncated run id for this experiment"""
        return self.id[:8]

    @property
    def short_hash(self) -> str:
        """Return the truncated hash for this experiment"""
        return self.hash[:8]

    @property
    def humanize_start_timestamp(self) -> datetime.datetime:
        """Return the human-readable start timestamp"""
        return humanize_utc_timestamp(self.experiment_start)

    @property
    def humanize_end_timestamp(self) -> datetime.datetime:
        """Return the human-readable start timestamp"""
        return humanize_utc_timestamp(self.experiment_end)

    def _compute_hash(self) -> None:
        """Hash the config filename to uniquely identify experiments"""
        if self.experiment_id:
            hasher = hashlib.sha256(usedforsecurity=False)
            hasher.update(str(self.experiment_id).encode('utf-8'))
            self.hash = hasher.hexdigest()

    def _build_treatments(self) -> None:
        """Build a representation of treatments defined in config"""
        treatment_section = self.config.treatments
        if treatment_section is None:
            return
            
        for treatment_dict in treatment_section:
            for treatment_name, treatment in treatment_dict.items():
                action = treatment.action
                params = treatment.params
                self.treatments[treatment_name] = self._build_treatment(
                    action=action, params=params, name=treatment_name, orchestrator=self.orchestrator
                )
                self.typed_treatments.append(TreatmentData(name=treatment_name, start=None, end=None))
                logger.debug("Successfully built treatment %s", self.treatments[treatment_name])
        logger.info(f"Built {len(self.treatments)} treatments: {self.treatments.keys()}")

    def _build_treatment(self, action, params, name, orchestrator) -> Treatment:
        """Build a single treatment from a description"""
        treatment_class = self.treatment_keys.get(action)
        if treatment_class is None:
            raise OxnException(
                message=f"Error while building treatment {name}",
                explanation=f"Treatment key {action} does not exist in the treatment library",
            )
        instance = treatment_class(config=params, name=name, orchestrator=orchestrator)
        return instance

    def _extend_treatments(self) -> None:
        """Extend the treatments the runner knows about with user-supplied treatments"""
        for treatment in self.additional_treatments:
            self.treatment_keys |= {treatment.action: treatment}

    def _get_runtime_treatments(self) -> List[Treatment]:
        return [
            treatment for treatment in self.treatments.values()
            if treatment.is_runtime()
        ]

    def _get_compile_time_treatments(self) -> List[Treatment]:
        return [
            treatment for treatment in self.treatments.values()
            if not treatment.is_runtime()
        ]

    def execute_compile_time_treatments(self) -> None:
        """Execute runtime treatments"""
        logger.info("Starting compile time treatments")
        for treatment in self._get_compile_time_treatments():
            treatment.start = datetime.datetime.now(datetime.timezone.utc)
            for i, v in enumerate(self.typed_treatments):
                if v.name == treatment.name:
                    self.typed_treatments[i].start = treatment.start
            treatment.inject()

    def clean_compile_time_treatments(self) -> None:
        logger.info("Cleaning compile time treatments")
        for treatment in self._get_compile_time_treatments():
            treatment.end = datetime.datetime.now(datetime.timezone.utc)
            for i, v in enumerate(self.typed_treatments):
                if v.name == treatment.name:
                    self.typed_treatments[i].end = treatment.end
            treatment.clean()

    def execute_runtime_treatments(self) -> List[TreatmentData]:
        """
        Execute one run of the experiment
        A single experiment run is defined as one execution of all treatments and one observation of all responses
        """
        if self.accountant:
            self.accountant.read_all_containers()
            self.accountant.read_oxn()
        ttw_left = self.observer.time_to_wait_left()
        logger.info(f"Sleeping for {ttw_left} seconds")
        time.sleep(ttw_left)
        logger.info(f"Starting runtime treatments")
        treatment_data = []
        for treatment in self._get_runtime_treatments():
            treatment_start = datetime.datetime.now(datetime.timezone.utc)
            treatment.inject()
            treatment.clean()
            treatment_end = datetime.datetime.now(datetime.timezone.utc)
            treatment_data.append(TreatmentData(name=treatment.name, start=treatment_start, end=treatment_end))
            self.treatments[treatment.name].start = treatment_start
            self.treatments[treatment.name].end = treatment_end
            for i, v in enumerate(self.typed_treatments):
                if v.name == treatment.name:
                    self.typed_treatments[i].start = treatment_start
                    self.typed_treatments[i].end = treatment_end
        logger.info(f"Injected treatments")
        return treatment_data

    def observe_response_variables(self) -> None:
        self.observer.initialize_variables()
        ttw_right = self.observer.time_to_wait_right()
        logger.info(f"Sleeping for {ttw_right} seconds")
        time.sleep(ttw_right)
        self.observer.observe()
        logger.info("Observed response variables")
        self._label()
        if self.accountant:
            self.accountant.read_all_containers()
            logger.debug(
                f"Read container resource data for {self.accountant.container_names}"
            )
            self.accountant.read_oxn()
            self.accountant.consolidate()

    def clear(self) -> None:
        """Clear the storage of the runner"""
        self.experiment_end = None
        self.experiment_start = None

    def _label(self) -> None:
        """Label the observed data with information from the treatments"""
        # Un-typed version
        """ for treatment in self.treatments.values():
            for response_id, response_variable in self.observer.variables().items():
                try:
                    response_variable.label(
                        treatment_end=treatment.end,
                        treatment_start=treatment.start,
                        label_column=treatment.name,
                        label=treatment.name,
                    )
                except (JaegerException, PrometheusException) as e:
                    logger.warning(f"Failed to label response variable {response_variable.name}: {str(e)}. Skipping.")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error while labeling response variable {response_variable.name}: {str(e)}")
                    raise """

        # Typed version
        for i, trtmnt in enumerate(self.typed_treatments):
            for response_id, response_variable in self.observer.variables().items():
                try:
                    response_variable.label(
                        treatment_end=trtmnt.end,
                        treatment_start=trtmnt.start,
                        label_column=trtmnt.name,
                        label=trtmnt.name,
                    )
                except (JaegerException, PrometheusException) as e:
                    logger.warning(f"Failed to label response variable {response_variable.name}: {str(e)}. Skipping.")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error while labeling response variable {response_variable.name} with treatment {trtmnt.name}: {str(e)}")
                    raise
