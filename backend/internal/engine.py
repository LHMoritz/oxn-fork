""" 
Purpose: Core logic for executing experiments.
Functionality: Manages the orchestration, execution, and observation of experiments.
Connection: Central component that coordinates between treatments, load generation, and response observation.

 """

import datetime
import logging
from typing import Tuple
import yaml
from jsonschema import validate
from pathlib import Path

from backend.internal.models.experiment import Experiment
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

    def __init__(self, spec: Experiment, id=None):
        self.id = id
        """The id of the experiment"""
        self.spec = spec
        """The loaded experiment specification"""
        self.reporter = Reporter()
        """A reference to a reporter instance"""
        self.orchestrator = KubernetesOrchestrator(experiment_config=spec)
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
        self.status = 'NOT_STARTED'
        self.error_message = None
        self.started_at = None
        self.completed_at = None
        # If you want to see the locust logs, set this to True
        self.doLocustLog = False
    def run(
        self,
        orchestration_timeout=120,
        randomize=False,
        accounting=False,
    ) -> Tuple[dict[str, ResponseVariable], dict[str, dict[str, dict[str, str]]]]:
        """Run an experiment 1 time"""
        self.generator = LocustFileLoadgenerator(
            orchestrator=self.orchestrator,
            config=self.spec.model_dump(mode="json"),
            log=self.doLocustLog,
            run_time=self.spec.loadgen.run_time
        )
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
        if not self.orchestrator.ready(timeout=orchestration_timeout):
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
        experiment_start = datetime.datetime.now(datetime.timezone.utc)
        self.runner.experiment_start = experiment_start.timestamp()
        self.runner.observer.experiment_start = experiment_start.timestamp()
        
        self.generator.start()
        self.loadgen_running = True
        logger.info("Started load generation")

        # Execute runtime treatments while load generation is running
        treatment_data = self.runner.execute_runtime_treatments()
        
        
        # Wait for load generation to complete its full duration
        logger.info("Waiting for load generation to complete")
        self.generator.stop()
        self.loadgen_running = False
        logger.info("Stopped load generation")

        experiment_end = datetime.datetime.now(datetime.timezone.utc)
        self.runner.experiment_end = experiment_end.timestamp()
        self.runner.observer.experiment_end = experiment_end.timestamp()

        # Clean up and observe results
        self.runner.clean_compile_time_treatments()
        self.runner.observe_response_variables()
        
        self.loadgen_running = False

        

        # Populate the report data: for each response variable, gather the interaction data for each treatment
        """
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
            ) """
        self.reporter.initialize_report_data(run_key=self.runner.short_id)
        logger.debug("Assembled all interaction data")
        self.reporter.add_loadgen_data(
            runner=self.runner, request_stats=self.generator.env.stats
        )
        self.reporter.add_experiment_data(experiment_start=experiment_start, experiment_end=experiment_end, runner=self.runner)
        # Now we return two dicts, one with the dataframes and one with the report. This data then gets written to disk by the caller (ExperimentManager)

        # Add treatment data to the report
        self.reporter.add_treatment_data(self.runner, treatment_data)

        return self.runner.observer.variables(), self.reporter.get_report_data()
