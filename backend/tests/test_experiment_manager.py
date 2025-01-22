from gevent import monkey
monkey.patch_all()

from math import log
import time
import unittest.mock
from venv import logger
import pytest
from pathlib import Path
import json
import shutil
import tempfile
from backend.internal.experiment_manager import ExperimentManager
import pandas as pd
from backend.internal.models.response import ResponseVariable
from backend.internal.responses import MetricResponseVariable, TraceResponseVariable
from backend.internal.store import DocumentStore, FileFormat
from unittest.mock import MagicMock, patch
import io 

@pytest.fixture
def test_dir():
    """Create a temporary directory for test data"""
    tmp_dir = Path(tempfile.mkdtemp())
    yield tmp_dir
    shutil.rmtree(tmp_dir)  # Cleanup after tests

@pytest.fixture
def mock_store():
    store = MagicMock(spec=DocumentStore)
    return store

@pytest.fixture
def experiment_manager(test_dir, mock_store):
    """Create ExperimentManager instance with test directory and mocked store"""
    return ExperimentManager(test_dir, mock_store)

@pytest.fixture
def sample_config():
    """Sample experiment configuration"""
    return {
        "experiment": {
            "name": "big",
            "version": "0.0.1",
            "orchestrator": "kubernetes",
            "services": {
                "jaeger": {
                    "name": "astronomy-shop-jaeger-query",
                    "namespace": "system-under-evaluation"
                },
                "prometheus": [
                    {
                        "name": "astronomy-shop-prometheus-server",
                        "namespace": "system-under-evaluation",
                        "target": "sue"
                    },
                    {
                        "name": "kube-prometheus-kube-prome-prometheus", 
                        "namespace": "oxn-external-monitoring",
                        "target": "oxn"
                    }
                ]
            },
            "responses": [
                {
                    "name": "frontend_traces",
                    "type": "trace", 
                    "service_name": "frontend",
                    "left_window": "10s",
                    "right_window": "10s",
                    "limit": 1
                },
                {
                    "name": "system_CPU",
                    "type": "metric",
                    "metric_name": "sum(rate(container_cpu_usage_seconds_total{namespace=\"system-under-evaluation\"}[1m]))",
                    "left_window": "10s",
                    "right_window": "10s",
                    "step": 1,
                    "target": "oxn"
                },
                {
                    "name": "recommendation_deployment_CPU",
                    "type": "metric",
                    "metric_name": "sum(rate(container_cpu_usage_seconds_total{namespace=\"system-under-evaluation\", pod=~\"astronomy-shop-recommendationservice.*\"}[90s])) by (pod)",
                    "left_window": "10s",
                    "right_window": "10s",
                    "step": 1,
                    "target": "oxn"
                }
            ],
            "treatments": [
                {
                    "name": "empty_treatment",
                    "action": "empty",
                    "params": { "duration": "1m" }
                }
            ],
            "sue": {
                "compose": "opentelemetry-demo/docker-compose.yml",
                "exclude": ["loadgenerator"],
                "required": [
                    { "namespace": "system-under-evaluation", "name": "astronomy-shop-prometheus-server" }
                ]
            },
            "loadgen": {
                "run_time": "20m",
                "max_users": 500,
                "spawn_rate": 50,
                "locust_files": ["/backend/locust/locust_basic_interaction.py", "/backend/locust/locust_otel_demo.py"],
                "target": { "name": "astronomy-shop-frontendproxy", "namespace": "system-under-evaluation", "port": 8080 }
            }
        }
    }

def test_create_experiment(experiment_manager, sample_config):
    """Test the creation of an experiment"""
    experiment = experiment_manager.create_experiment(name="Test Experiment", config=sample_config)
    assert experiment is not None
    assert experiment['name'] == "Test Experiment"
    assert experiment['status'] == "PENDING"
    assert experiment['spec'] == sample_config

def test_create_batch_experiment(experiment_manager, sample_config):
    """Test the creation of a batch experiment"""
    parameter_variations = {"experiment.treatments.0.params.duration": "2m"}
    batch_config = experiment_manager.create_batch_experiment("Batch Test", sample_config, parameter_variations)
    assert batch_config is not None
    assert batch_config['name'] == "Batch Test"
    assert batch_config['status'] == "PENDING"
    assert batch_config['parameter_variations'] == parameter_variations

def test_get_experiment_config(experiment_manager, sample_config):
    """Test for get_experiment_config method"""
    experiment_id = "test_experiment"
    experiment_manager.store.load.return_value = sample_config
    config = experiment_manager.get_experiment_config(experiment_id)
    experiment_manager.store.load.assert_called_once_with(f"{experiment_id}_config", FileFormat.JSON)
    assert config == sample_config

def test_run_batch_experiment(experiment_manager):
    """Test running a batch experiment"""
    batch_id = "batch_1"
    experiment_manager.store.load.return_value = [{'sub_experiment_id': 0}]
    experiment_manager.run_experiment = MagicMock()
    experiment_manager.run_batch_experiment(batch_id, ['json'], 1)
    experiment_manager.run_experiment.assert_called_once()

def test_get_experiment_report(experiment_manager):
    """Test getting an experiment report"""
    experiment_id = "test_experiment"
    experiment_manager.store.load.return_value = {'report': 'data'}
    report = experiment_manager.get_experiment_report(experiment_id)
    assert report['report'] == 'data'
    experiment_manager.store.load.assert_called_once_with(f"{experiment_id}_report", FileFormat.YAML)

def test_run_experiment(experiment_manager, sample_config):
    """Test running an experiment"""
    experiment_id = "test_experiment"
    experiment_manager.acquire_lock = MagicMock(return_value=True)
    experiment_manager.release_lock = MagicMock()
    experiment_manager.update_experiment_config = MagicMock()
    experiment_manager.get_experiment_config = MagicMock(return_value={'spec': sample_config})
    experiment_manager.run_experiment(experiment_id, ['json'], 1)
    experiment_manager.update_experiment_config.assert_any_call(experiment_id, {'status': 'RUNNING'})
    experiment_manager.update_experiment_config.assert_any_call(experiment_id, {'status': 'COMPLETED'})

def test_update_experiment_config(experiment_manager, sample_config):
    """Test updating experiment config"""
    experiment_id = "test_experiment"
    experiment_manager.store.load.return_value = sample_config
    experiment_manager.update_experiment_config(experiment_id, {'status': 'UPDATED'})
    experiment_manager.store.save.assert_called_once()

def test_list_experiments(experiment_manager, sample_config):
    """Test listing all experiments"""
    experiment_manager.store.list_keys.return_value = ['1_config']
    experiment_manager.store.load.return_value = sample_config
    experiments = experiment_manager.list_experiments()
    assert '1_config' in experiments

def test_acquire_lock(experiment_manager, test_dir):
    """Test acquiring a lock"""
    lock_file_path = test_dir / '.lock'
    experiment_manager.lock_file = lock_file_path
    with open(lock_file_path, 'w') as f:
        pass
    assert experiment_manager.acquire_lock() is True
    experiment_manager.release_lock()
    assert not hasattr(experiment_manager, 'lock_fd')

def test_release_lock(experiment_manager, test_dir):
    """Test releasing a lock"""
    lock_file_path = test_dir / '.lock'
    experiment_manager.lock_file = lock_file_path
    with open(lock_file_path, 'w') as f:
        pass
    experiment_manager.acquire_lock()
    experiment_manager.release_lock()
    assert not hasattr(experiment_manager, 'lock_fd')

def test_get_experiment_response_data(experiment_manager):
    """Test getting experiment response data"""
    experiment_manager.store.list_keys.return_value = ['1_0_response.json']
    experiment_manager.store.load.return_value = {'data': 'response'}
    response = experiment_manager.get_experiment_response_data(0, '1', 'response', 'json')
    assert response['data'] == 'response'

def test_get_experiment_data(experiment_manager):
    """Test getting experiment data"""
    experiment_manager.store.list_files.return_value = ['1_report.yaml']
    experiment_manager.store.load.return_value = {'report': 'data'}
    data = experiment_manager.get_experiment_data('1')
    assert isinstance(data, io.BytesIO)

def test_get_batched_experiment_id_by_params(experiment_manager):
    """Test getting batched experiment ID by parameters"""
    experiment_manager.store.load.return_value = [{'sub_experiment_id': '0', 'param': 1}]
    sub_experiment_id = experiment_manager.get_batched_experiment_id_by_params('batch_1', {'param': 1})
    assert sub_experiment_id == '0'

def test_get_batched_experiment_report(experiment_manager):
    """Test getting batched experiment report"""
    experiment_manager.store.load.return_value = {'report': 'data'}
    report = experiment_manager.get_batched_experiment_report('batch_1', '0')
    assert report['report'] == 'data'

def test_get_batched_experiment_response_data(experiment_manager):
    """Test getting batched experiment response data"""
    experiment_manager.store.load.return_value = {'response': 'data'}
    response = experiment_manager.get_batched_experiment_response_data('batch_1', '0', 'response', 'json')
    assert response['response'] == 'data'