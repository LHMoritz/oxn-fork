from datetime import datetime
from typing import Dict, List
import logging
from backend.internal.fault_detection import DetectionEvent, InjectedFault, FaultDetectionAnalyzer

logger = logging.getLogger(__name__)

class ExperimentAnalyzer:
    """Service for analyzing experiment results"""
    
    def __init__(self, detection_analyzer: FaultDetectionAnalyzer):
        self.detection_analyzer = detection_analyzer
    
    def extract_faults_from_report(self, report: Dict) -> List[InjectedFault]:
        """Extract fault information from experiment report"""
        faults = []
        seen_treatments = set()
        
        # Get the first (and usually only) run
        run_id = next(iter(report['report']['runs']))
        run_data = report['report']['runs'][run_id]
        
        for interaction in run_data['interactions'].values():
            treatment_name = interaction['treatment_name']
            if treatment_name in seen_treatments:
                continue
                
            seen_treatments.add(treatment_name)
            faults.append(InjectedFault(
                name=treatment_name,
                start_time=interaction['treatment_start'],
                end_time=interaction['treatment_end'],
                type=interaction['treatment_type'],
                params={}  # TODO: Add treatment params
            ))
        
        return faults
    
    def analyze_fault_detection(self, report: Dict) -> List[Dict]:
        """Analyze fault detection for an experiment"""
        faults = self.extract_faults_from_report(report)
        return self.detection_analyzer.analyze_experiment(faults)

    def get_raw_detection_data(self, start_time: datetime, end_time: datetime) -> dict:
        """Get raw detection data from the underlying system"""
        return self.detection_analyzer.get_raw_detection_data(start_time, end_time)
