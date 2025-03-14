class OxnException(Exception):
    """Custom exception subclass to represent errors arising from oxn to enforce system boundaries"""

    def __init__(self, message: object = None, explanation: object = None) -> object:
        """Provide additional exception explanation"""
        self.explanation = explanation
        self.message = message
        super(OxnException, self).__init__(message)

    def __str__(self):
        message = super(OxnException, self).__str__()
        if self.explanation:
            message = f"{message}: {self.explanation}"
        return message


class JaegerException(OxnException):
    """Custom exception subclass to enforce system boundaries with respect to Jaeger"""

    pass


class PrometheusException(OxnException):
    """Custom exception subclass to enforce system boundaries with respect to Prometheus"""

    pass


class OrchestrationException(OxnException):
    """Custom exception subclass to enforce system boundaries with respect to the DockerComposeOrchestrator"""

    pass


class LocustException(OxnException):
    """Custom exception subclass to enforce system boundaries with respect to Locust"""
    pass

class OrchestratorException(OxnException):
    """Custom exception subclass to enforce system boundaries with respect to Orchestrator"""
    pass
class OrchestratorResourceNotFoundException(OxnException):
    """Custom exception subclass to enforce system boundaries with respect to Orchestrator resource not found"""
    pass

class StoreException(OxnException):
    """Custom exception subclass to enforce system boundaries with respect to Store"""
    pass
