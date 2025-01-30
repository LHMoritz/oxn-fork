from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List
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

@dataclass
class DetectionAnalysisResult:
    """Represents the result of analyzing a fault detection"""
    fault_name: str
    detected: bool
    detection_time: str | None
    detection_latency: float | None
    true_positives: List[Dict]
    false_positives: List[Dict]
    def to_dict(self) -> dict:
        """Convert the dataclass instance to a dictionary"""
        return asdict(self)