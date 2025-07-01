from abc import ABC, abstractmethod

class IntegrationBase(ABC):
    @abstractmethod
    def parse_input(self, event):
        pass

    @abstractmethod
    def build_response(self, message):
        pass
