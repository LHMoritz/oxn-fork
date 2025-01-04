""" 
Purpose: Core logic for executing experiments.
Functionality: Manages the orchestration, execution, and observation of experiments.
Connection: Central component that coordinates between treatments, load generation, and response observation.

 """

import logging
from typing import Tuple
import yaml
from jsonschema import validate
from pathlib import Path

from backend.internal.models.response import ResponseVariable
from backend.internal.runner import ExperimentRunner
from backend.internal.docker_orchestration import DockerComposeOrchestrator
from backend.internal.kubernetes_orchestrator import KubernetesOrchestrator
from backend.internal.report import Reporter
from backend.internal.locust_file_loadgenerator import LocustFileLoadgenerator
from backend.internal.utils import utc_timestamp
from backend.internal.errors import OxnException, OrchestrationException

logger = logging.getLogger(__name__)

class Engine:
    """
    Observability experiments engine

    This class encapsulates all behavior needed to execute observability experiments.
    """

    def __init__(self, orchestrator_class=None, spec=None, id=None):
        self.id = id
        """The id of the experiment"""
        self.spec = spec
        """The loaded experiment specification"""
        self.reporter = Reporter()
        """A reference to a reporter instance"""
        self.orchestrator = orchestrator_class or KubernetesOrchestrator
        """A reference to an orchestrator instance"""
        self.generator = None
        """A reference to a load generator instance"""
        self.runner = None
        """A reference to a runner instance"""
        self.loadgen_running = False
        """Status of the load generator"""
        self.sue_running = False
        """Status of the sue"""
        self.additional_treatments = []
        self.status = 'PENDING'
        self.error_message = None
        self.started_at = None
        self.completed_at = None
        # If you want to see the locust logs, set this to True
        self.doLocustLog = False
    def run(
        self,
        orchestration_timeout=None,
        randomize=False,
        accounting=False,
    ) -> Tuple[dict[str, ResponseVariable], dict[str, dict[str, dict[str, str]]]]:
        """Run an experiment 1 time"""
        assert self.spec
        assert self.spec["experiment"]
        assert self.spec["experiment"]["orchestrator"]
        self.generator = LocustFileLoadgenerator(orchestrator=self.orchestrator, config=self.spec, log=self.doLocustLog)
        names = []
        self.runner = ExperimentRunner(
            config=self.spec,
            experiment_id=self.id,
            additional_treatments=self.additional_treatments,
            random_treatment_order=randomize,
            accountant_names=names,
            orchestrator=self.orchestrator,
        )
        self.runner.execute_compile_time_treatments()
        self.orchestrator.orchestrate()
        if not self.orchestrator.ready(expected_services=None, timeout=orchestration_timeout):
            self.runner.clean_compile_time_treatments()
            self.orchestrator.teardown()
            raise OrchestrationException(
                message="Error while building the sue",
                explanation=f"Could not build the sue within {orchestration_timeout}",
            )
        self.sue_running = True
        logger.info("Started sue")
        for treatment in self.runner.treatments.values():
            if not treatment.preconditions():
                raise OxnException(
                    message=f"Error while checking preconditions for treatment {treatment.name} which is class {treatment.__class__}",
                    explanation="\n".join(treatment.messages),
                )
        self.generator.start()
        logger.info("Started load generation")
        self.loadgen_running = True
        experiment_start = utc_timestamp()
        self.runner.experiment_start = experiment_start
        self.runner.observer.experiment_start = experiment_start
        self.runner.execute_runtime_treatments()
        self.runner.clean_compile_time_treatments()
        self.runner.experiment_end = utc_timestamp()
        self.runner.observer.experiment_end = self.runner.experiment_end
        # This runs all of the queries (prometheus, jaeger) at the end, populates self.runner.observer.variables().items()
        # It sleeps and blocks and then runs the observe() function
        # of every response variable. All of the data is stored in memory and written to disk at once.
        # If memory footprint becomes an issue, we can refactor to write the data to disk sequentially.
        self.runner.observe_response_variables()
        self.generator.stop()
        self.loadgen_running = False
        logger.info("Stopped load generation")

        

        #return self.runner.observer.variables(), self.reporter.report_data

        # Populate the report data: for each response variable, gather the interaction data for each treatment
        for _, response in self.runner.observer.variables().items():
            for _, treatment in self.runner.treatments.items():
                self.reporter.gather_interaction(
                    experiment=self.runner,
                    treatment=treatment,
                    response=response,
                )
                logger.debug(
                    f"Gathered interaction data for {treatment} and {response}"
                )
            self.reporter.assemble_interaction_data(
                run_key=self.runner.short_id
            )
            logger.debug("Assembled all interaction data")
            self.reporter.add_loadgen_data(
                runner=self.runner, request_stats=self.generator.env.stats
            )
            self.reporter.add_experiment_data(runner=self.runner)
        # Now we return two dicts, one with the dataframes and one with the report. This data then gets written to disk by the caller (ExperimentManager)

        return self.runner.observer.variables(), self.reporter.get_report_data()
