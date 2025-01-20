

class BatchExperimentsNotSupported(Exception):
    def __init__(self, message):
        super().__init__(message)


class OXNFileNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)

class LabelNotPresent(Exception):
    def __init__(self, message):
        super().__init__(message)
