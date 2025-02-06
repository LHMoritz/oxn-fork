from gevent import monkey

from backend.internal.models.experiment import Experiment
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

def sample_config():
    """Sample experiment configuration"""
    return {
    "name": "latest",
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
        "name": "accountingservice_traces",
        "type": "trace",
        "service_name": "accountingservice",
        "left_window": "10s",
        "right_window": "10s",
        "limit": 1499
      },
      {
        "name": "flagd_traces",
        "type": "trace",
        "service_name": "flagd",
        "left_window": "10s",
        "right_window": "10s",
        "limit": 1499
      },
      {
        "name": "cpu_usage",
        "type": "metric",
        "metric_name": "sum(rate(node_cpu_seconds_total{mode!=\"idle\"}[1m])) by (instance)",
        "left_window": "10s",
        "right_window": "10s",
        "step": 1,
        "target": "sue"
      },
      {
        "name": "tcp_connections",
        "type": "metric",
        "metric_name": "node_netstat_Tcp_CurrEstab",
        "left_window": "10s",
        "right_window": "10s",
        "step": 1,
        "target": "sue"
      }
    ],
    "treatments": [
      {
        "kubernetes_prometheus_rules": {
          "action": "kubernetes_prometheus_rules",
          "params": {
            "latency_threshold": 100,
            "evaluation_window": "120s"
          }
        }
      },

      {
        "add_security_context": {
          "action": "security_context_kubernetes",
          "params": {
            "namespace": "system-under-evaluation",
            "label_selector": "app.kubernetes.io/component",
            "label": "recommendationservice",
            "capabilities": {
              "add": [
                "NET_ADMIN"
              ]
            }
          }
        }
      },
      {
        "delay_treatment": {
          "action": "delay",
          "params": {
            "namespace": "system-under-evaluation",
            "label_selector": "app.kubernetes.io/name",
            "label": "astronomy-shop-recommendationservice",
            "delay_time": "120ms",
            "delay_jitter": "120ms",
            "duration": "1m",
            "interface": "eth0"
          }
        }
      }
    ],
    "sue": {
      "compose": "opentelemetry-demo/docker-compose.yml",
      "exclude": [
        "loadgenerator"
      ],
      "required": [
        {
          "namespace": "system-under-evaluation",
          "name": "astronomy-shop-prometheus-server"
        }
      ]
    },
    "loadgen": {
      "run_time": "3m",
      "max_users": 500,
      "spawn_rate": 50,
      "locust_files": [
        "/backend/locust/locust_basic_interaction.py",
        "/backend/locust/locust_otel_demo.py"
      ],
      "target": {
        "name": "astronomy-shop-frontendproxy",
        "namespace": "system-under-evaluation",
        "port": 8080
      }
    }
  }

@pytest.fixture
def ExperimentConfig():
    return Experiment(**sample_config())


def test_create_experiment(experiment_manager, ExperimentConfig):
    """Test the creation of an experiment"""
    experiment = experiment_manager.create_experiment(name="Test Experiment", config=ExperimentConfig)
    assert experiment is not None
    assert experiment.id is not None
    assert experiment.name == "Test Experiment"
    assert experiment.status == "NOT_STARTED"
    assert experiment.error_message is ""
    assert experiment.spec == ExperimentConfig

def test_create_batch_experiment(experiment_manager, ExperimentConfig):
    """Test the creation of a batch experiment"""
    parameter_variations = {"treatments.2.delay_treatment.params.delay_time": "2m", "treatments.2.delay_treatment.params.delay_jitter": "2m"}
    batch_config = experiment_manager.create_batch_experiment("Batch Test", ExperimentConfig, parameter_variations)
    assert batch_config is not None
    assert batch_config.name == "Batch Test"
    assert batch_config.status == "NOT_STARTED"
    assert batch_config.parameter_variations == parameter_variations

def test_get_experiment_config(experiment_manager, ExperimentConfig):
    """Test for get_experiment_config method"""
    # Create an experiment
    response = experiment_manager.create_experiment(name="Test Experiment", config=ExperimentConfig)
    experiment_id = response.id

    # Mock the store.load to return a config with the expected structure
    experiment_manager.store.load.return_value = {
        'spec': ExperimentConfig.model_dump(mode="json")
    }

    # Get the experiment config
    config = experiment_manager.get_experiment_config(experiment_id)
    
    # Verify the store was called correctly
    experiment_manager.store.load.assert_called_once_with(f"{experiment_id}_config", FileFormat.JSON)
    
    # Verify the returned config matches the original
    assert config.model_dump(mode="json") == ExperimentConfig.model_dump(mode="json")

def test_get_experiment_report(experiment_manager):
    """Test getting an experiment report"""
    experiment_id = "test_experiment"
    experiment_manager.store.load.return_value = {'report': 'data'}
    report = experiment_manager.get_experiment_report(experiment_id)
    assert report['report'] == 'data'
    experiment_manager.store.load.assert_called_once_with(f"{experiment_id}_report", FileFormat.YAML)

def test_update_experiment_config(experiment_manager, ExperimentConfig):
    """Test updating experiment config"""
    # Create an experiment first
    response = experiment_manager.create_experiment(name="Test Experiment", config=ExperimentConfig)
    experiment_id = response.id

    # Mock the store.load to return the actual created config
    experiment_manager.store.load.return_value = {
        'id': experiment_id,
        'name': "Test Experiment",
        'status': 'NOT_STARTED',
        'created_at': response.created_at,
        'started_at': "",
        'completed_at': "",
        'error_message': "",
        'spec': ExperimentConfig.model_dump(mode="json")
    }

    # Update the experiment config
    experiment_manager.update_experiment_config(experiment_id, {'status': 'UPDATED'})

    # Verify the store.save was called with the correct updated config
    expected_config = {
        'id': experiment_id,
        'name': "Test Experiment",
        'status': 'UPDATED',  # This should be updated
        'created_at': response.created_at,
        'started_at': "",
        'completed_at': "",
        'error_message': "",
        'spec': ExperimentConfig.model_dump(mode="json")
    }
    
    experiment_manager.store.save.assert_called_with(
        f"{experiment_id}_config",
        expected_config,
        FileFormat.JSON
    )

def test_list_experiments(experiment_manager, ExperimentConfig):
    """Test listing all experiments"""
    experiment_manager.store.list_keys.return_value = ['1_config', '2_config', '3_config']
    experiment_manager.store.load.return_value = ExperimentConfig.model_dump(mode="json")
    experiments = experiment_manager.list_experiments_status()
    assert len(experiments) == 3
    
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
    