"""Header file to expose modules at the package root."""

# Package metadata
__version__ = "1.0a"

__title__ = "dockertest"
__description__ = "Facilities to manipulate docker containers for tests in python."

__author__ = "Fernando Silveira"
__email__ = "fernando@f14a.com"

__license__ = "MIT"
__copyright__ = "Copyright (c) 2016 Fernando Silveira"


# Public interface
from .base import Container, run_container, stop_container
from .servicetest import ServiceTest, HttpServiceTest

# Hide submodule details
del base
del servicetest
