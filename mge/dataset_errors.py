"""Dataset validity is separate from mutation settlement and publish policy."""


class MgeDatasetError(RuntimeError):
    def __init__(self, state: str, stage: str):
        self.state = state
        self.stage = stage
        super().__init__("MGE data could not be verified. Existing boards have been retained.")
