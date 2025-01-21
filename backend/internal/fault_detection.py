from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Protocol
import logging

logger = logging.getLogger(__name__)

@dataclass
class DetectionEvent:
    """Represents a detection of a fault"""
    name: str
    firing_time: datetime
    severity: str
    labels: Dict

@dataclass
class InjectedFault:
    """Represents a fault that was injected"""
    name: str
    start_time: datetime
    end_time: datetime
    type: str
    params: Dict

class FaultDetectionAnalyzer(ABC):
    """Base class for fault detection analysis"""
    
    @abstractmethod
    def get_detections(self, start_time: datetime, end_time: datetime) -> List[DetectionEvent]:
        """Get all detections in the given time window"""
        pass
    
    @abstractmethod
    def analyze_detection(self, fault: InjectedFault, detections: List[DetectionEvent]) -> Dict:
        """Analyze if and when a fault was detected"""
        pass
    
    def analyze_experiment(self, faults: List[InjectedFault]) -> List[Dict]:
        """Analyze detection for all faults in an experiment"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        logger.info(f"Analyzing experiment from {start_time} to {end_time}")
        logger.info(f"Number of faults to analyze: {len(faults)}")
        
        detections = self.get_detections(start_time, end_time)
        logger.info(f"Found {len(detections)} total detections")
        
        results = []
        for fault in faults:
            logger.debug(f"Analyzing fault: {fault.name} ({fault.type})")
            result = self.analyze_detection(fault, detections)
            results.append(result)
            if result['detected']:
                logger.info(f"Fault {fault.name} was detected after {result['detection_latency']}s")
            else:
                logger.warning(f"Fault {fault.name} was not detected")
        
        return results

class PrometheusDetectionAnalyzer(FaultDetectionAnalyzer):
    """Prometheus-specific implementation of fault detection analysis"""
    
    def __init__(self, prometheus):
        self.prometheus = prometheus
        logger.info("Initialized PrometheusDetectionAnalyzer")
    
    def get_detections(self, start_time: datetime, end_time: datetime) -> List[DetectionEvent]:
        """Get detections from Prometheus alerts"""
        logger.debug(f"Fetching alerts from {start_time} to {end_time}")
        alert_data = self.prometheus.get_alerts(start_time, end_time)
        return self._process_alerts(alert_data, start_time, end_time)
    
    def _process_alerts(self, alert_data: dict, start_time: datetime, end_time: datetime) -> List[DetectionEvent]:
        """Process alert results from Prometheus query"""
        detections = []
        results = alert_data.get('data', {}).get('result', [])
        logger.debug(f"Processing {len(results)} alert results")
        
        for result in results:
            metric = result['metric']
            values = result['values']
            alert_name = metric.get('alertname', 'unknown')
            
            # Skip system alerts
            if alert_name in [
                "PrometheusTargetMissing", 
                "PrometheusJobMissing",
                "PrometheusAlertmanagerJobMissing",
                "PrometheusAlertmanagerE2eDeadManSwitch"
            ]:
                logger.debug(f"Skipping system alert: {alert_name}")
                continue
            
            alert_state = metric.get('alertstate', '')
            logger.debug(f"Processing alert {alert_name} in state {alert_state}")
            
            for timestamp, value in values:
                event_time = datetime.fromtimestamp(timestamp)
                if (float(value) > 0 and 
                    alert_state == "firing" and
                    start_time <= event_time <= end_time):
                    detections.append(DetectionEvent(
                        name=alert_name,
                        firing_time=event_time,
                        severity=metric.get('severity', 'none'),
                        labels=metric
                    ))
                    logger.debug(f"Added detection for {alert_name} at {event_time}")
        
        logger.info(f"Found {len(detections)} valid detections")
        return detections
    
    def analyze_detection(self, fault: InjectedFault, detections: List[DetectionEvent]) -> Dict:
        """Analyze if and when a fault was detected"""
        logger.debug(f"Analyzing detection for fault {fault.name} from {fault.start_time} to {fault.end_time}")
        
        relevant_detections = [
            d for d in detections 
            if fault.start_time <= d.firing_time <= fault.end_time + timedelta(minutes=1)
        ]
        
        logger.debug(f"Found {len(relevant_detections)} relevant detections")
        
        if not relevant_detections:
            logger.warning(f"No detections found for fault {fault.name}")
            return {
                'fault_name': fault.name,
                'detected': False,
                'detection_time': None,
                'detection_latency': None,
                'alerts_triggered': []
            }
        
        first_detection = min(relevant_detections, key=lambda d: d.firing_time)
        detection_latency = (first_detection.firing_time - fault.start_time).total_seconds()
        
        logger.info(f"Fault {fault.name} detected after {detection_latency}s with alert {first_detection.name}")
        
        return {
            'fault_name': fault.name,
            'detected': True,
            'detection_time': first_detection.firing_time.isoformat(),
            'detection_latency': detection_latency,
            'alerts_triggered': [
                {
                    'name': d.name,
                    'time': d.firing_time.isoformat(),
                    'severity': d.severity,
                    'labels': d.labels
                } for d in relevant_detections
            ]
        } 