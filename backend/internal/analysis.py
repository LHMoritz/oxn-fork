from datetime import datetime
from typing import Dict, List
import logging
from backend.internal.fault_detection import DetectionAnalysisResult, DetectionEvent, InjectedFault, FaultDetectionAnalyzer

logger = logging.getLogger(__name__)

class ExperimentAnalyzer:
    """Service for analyzing experiment results"""
    
    def __init__(self, detection_analyzer: FaultDetectionAnalyzer):
        self.detection_analyzer = detection_analyzer
    
    def extract_faults_from_report(self, report: Dict) -> List[InjectedFault]:
        """Extract fault information from experiment report"""
        faults = []
        
        
        # Process all runs in the report
        for run_id, run_data in report['report']['runs'].items():
            logger.debug(f"Processing run {run_id}")
            seen_treatments = set()
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
        
        logger.info(f"Extracted {len(faults)} unique faults from {len(report['report']['runs'])} runs")
        return faults
    
    def extract_experiment_start_time(self, report: Dict) -> datetime:
        """Extract the start time of the experiment from the report"""
        try:
            if 'experiment_start' not in report.get('report', {}):
                raise KeyError("'experiment_start' field not found in report")
            
            start_time = report['report']['experiment_start']
            # If already a datetime object, return it directly
            if isinstance(start_time, datetime):
                return start_time
            # Otherwise parse the string
            # example 2025-01-22 13:15:35.411717
            return datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S.%f')
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to extract start time from report: {e}")
            raise ValueError(f"Invalid report format - missing or invalid experiment_start: {e}")
    
    def extract_experiment_end_time(self, report: Dict) -> datetime:
        """Extract the end time of the experiment from the report"""
        try:
            if 'experiment_end' not in report.get('report', {}):
                raise KeyError("'experiment_end' field not found in report")
            
            end_time = report['report']['experiment_end']
            # If already a datetime object, return it directly
            if isinstance(end_time, datetime):
                return end_time
            # Otherwise parse the string
            # example 2025-01-22 13:15:35.411717
            return datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S.%f')
        except (KeyError, TypeError) as e:
            logger.error(f"Failed to extract end time from report: {e}")
            raise ValueError(f"Invalid report format - missing or invalid experiment_end: {e}")
    
    def analyze_fault_detection(self, report: Dict) -> List[DetectionAnalysisResult]:
        """Analyze fault detection for an experiment"""
        faults = self.extract_faults_from_report(report)
        start_time = self.extract_experiment_start_time(report)
        end_time = self.extract_experiment_end_time(report)
        logger.info(f"Analyzing faults  from {start_time} to {end_time}")
        return self.detection_analyzer.analyze_experiment(faults, start_time, end_time)

    def get_raw_detection_data(self, start_time: datetime, end_time: datetime) -> dict:
        """Get raw detection data from the underlying system"""
        return self.detection_analyzer.get_raw_detection_data(start_time, end_time)
