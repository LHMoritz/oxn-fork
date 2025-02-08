from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List
import logging
from backend.internal.prometheus import Prometheus
from backend.internal.models.fault_detection import DetectionEvent, InjectedFault, DetectionAnalysisResult
logger = logging.getLogger(__name__)
    

class FaultDetectionAnalyzer(ABC):
    """Base class for fault detection analysis"""

    @abstractmethod
    def get_raw_detection_data(self, start_time: datetime, end_time: datetime) -> dict:
        """Get raw detection data from the underlying system"""
        pass
    
    @abstractmethod
    def get_detections(self, start_time: datetime, end_time: datetime) -> List[DetectionEvent]:
        """Get all detections in the given time window"""
        pass
    
    @abstractmethod
    def analyze_detection(self, fault: InjectedFault, detections: List[DetectionEvent]) -> DetectionAnalysisResult:
        """Analyze if and when a fault was detected"""
        pass
    
    def analyze_experiment(self, faults: List[InjectedFault], start_time: datetime, end_time: datetime) -> List[DetectionAnalysisResult]:
        """Analyze detection for all faults in an experiment"""
        logger.info(f"Analyzing experiment from {start_time} to {end_time}")
        logger.info(f"Number of faults to analyze: {len(faults)}")
        
        detections = self.get_detections(start_time, end_time)
        logger.info(f"Found {len(detections)} total detections")
        
        results = []
        for fault in faults:
            logger.debug(f"Analyzing fault: {fault.name} ({fault.type})")
            result = self.analyze_detection(fault, detections)
            results.append(result)
        
        return results

class PrometheusDetectionAnalyzer(FaultDetectionAnalyzer):
    """Prometheus-specific implementation of fault detection analysis"""
    
    def __init__(self, prometheus: Prometheus):
        self.prometheus = prometheus
        logger.info("Initialized PrometheusDetectionAnalyzer with base URL: %s", prometheus.base_url)

    def get_raw_detection_data(self, start_time: datetime, end_time: datetime) -> dict:
        """Get raw detection data from Prometheus"""
        return self.prometheus.get_alerts(start_time, end_time)
    
    def get_detections(self, start_time: datetime, end_time: datetime) -> List[DetectionEvent]:
        """Get detections from Prometheus alerts"""
        logger.info(f"Fetching alerts from {start_time} to {end_time}")
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
    
    def analyze_detection(self, fault: InjectedFault, detections: List[DetectionEvent]) -> DetectionAnalysisResult:
        """Analyze if and when a fault was detected"""
        logger.debug(f"Analyzing detection for fault {fault.name} from {fault.start_time} to {fault.end_time}")
        
        true_positives = [
            d for d in detections 
            if fault.start_time <= d.firing_time <= fault.end_time
        ]

        false_positives = [
            d for d in detections 
            if d.firing_time < fault.start_time or d.firing_time > fault.end_time
        ]
        
        logger.debug(f"Found {len(true_positives)} true positives and {len(false_positives)} false positives")
        
        if not true_positives:
            logger.warning(f"No detections found for fault {fault.name}")
            return DetectionAnalysisResult(
                fault_name=fault.name,
                start_time=fault.start_time,
                end_time=fault.end_time,
                detected=False,
                detection_time=None,
                detection_latency=None,
                true_positives=[],
                false_positives=[{
                    'name': d.name,
                    'time': d.firing_time.isoformat(),
                    'severity': d.severity,
                    'labels': d.labels
                } for d in false_positives]
            )
        
        first_detection = min(true_positives, key=lambda d: d.firing_time)
        detection_latency = (first_detection.firing_time - fault.start_time).total_seconds()
        
        logger.info(f"Fault {fault.name} detected after {detection_latency}s with alert {first_detection.name}")
        
        return DetectionAnalysisResult(
            fault_name=fault.name,
            start_time=fault.start_time,
            end_time=fault.end_time,
            detected=True,
            detection_time=first_detection.firing_time.isoformat(),
            detection_latency=detection_latency,
            true_positives=[{
                'name': d.name,
                'time': d.firing_time.isoformat(),
                'severity': d.severity,
                'labels': d.labels
            } for d in true_positives],
            false_positives=[{
                'name': d.name,
                'time': d.firing_time.isoformat(),
                'severity': d.severity,
                'labels': d.labels
            } for d in false_positives]
        )
