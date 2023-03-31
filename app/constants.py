from enum import Enum


class Environment(str, Enum):
    LOCAL = "LOCAL"
    TESTING = "TESTING"
    PRODUCTION = "PRODUCTION"

    @property
    def is_testing(self):
        return self == self.TESTING
