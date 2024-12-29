import json

def update_dict_with_parameter_variations(config: dict, parameter_variations: dict) -> dict:
    """
    Updates a nested dictionary with parameter variations specified in dot notation.
    
    Args:
        config: The original configuration dictionary to update
        parameter_variations: Dictionary with keys in dot notation and values to update
        
    Example parameter_variations:
    {
        "experiment.treatments.0.params.duration": "1m",
        "experiment.treatments.0.params.delay": 10
    }
    
    Returns:
        Updated configuration dictionary
        
    Raises:
        KeyError: If a key in the path does not exist in the original config
        IndexError: If an array index is out of bounds
    """
    config = config.copy()
    
    for param_path, value in parameter_variations.items():
        # Split the path into parts
        path_parts = param_path.split('.')
        
        # Start at the root of the config
        current = config
        
        # Traverse to the second-to-last part to get the parent
        for part in path_parts[:-1]:
            # Handle array indices
            if part.isdigit():
                part = int(part)
                if not isinstance(current, list):
                    raise KeyError(f"Expected list but found {type(current)} at path {param_path}")
                if part >= len(current):
                    raise IndexError(f"Index {part} is out of bounds for list of length {len(current)} at path {param_path}")
            
            # Check if key exists in dict
            elif isinstance(part, str):
                if part not in current:
                    raise KeyError(f"Key '{part}' not found in config at path {param_path}")
                
            current = current[part]
            
        # Set the final value
        if path_parts[-1] not in current and not isinstance(current, list):
            raise KeyError(f"Final key '{path_parts[-1]}' not found in config at path {param_path}")
            
        current[path_parts[-1]] = value
        
    return config

def main():
    # Example config dict
    config = {
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
              "duration": "2m",
              "interface": "eth0"
            }
          }
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

    # Example parameter variations
    parameter_variations = {
        "experiment.treatments.1.delay_treatment.params.duration": "99m",
        "experiment.treatments.1.delay_treatment.params.delay_time": "99m",
        "experiment.treatments.1.delay_treatment.params.delay_jitter": "99m",
    }

    # Test the function
    updated_config = update_dict_with_parameter_variations(config, parameter_variations)
    print("Original config:")
    print(json.dumps(config, indent=4))
    print("\nUpdated config:")
    print(json.dumps(updated_config, indent=4))

if __name__ == "__main__":
    main()
