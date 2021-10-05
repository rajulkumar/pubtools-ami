import logging
import threading

from pubtools._ami.rhsm import RHSMClient
from pubtools._ami.arguments import from_environ
from .base import Service

LOG = logging.getLogger("pubtools.ami")

class RHSMClientService(Service):
    """ A service providing RHSM client.

    A client will be available only when RHSM url and
    certificates are provided.
    """

    def __init__(self, *args, **kwargs):
        self._lock = threading.Lock()
        self._instance = None
        super(RHSMClientService, self).__init__(*args, **kwargs)

    def add_service_args(self, parser):
        super(RHSMClientService, self).add_service_args(parser)

        group = parser.add_argument_group("RHSM environment")

        group.add_argument("--rhsm-url", help="Base URL of the RHSM API")
        group.add_argument("--rhsm-cert",
                            help=("RHSM API certificate path",
                                  "(or set RHSM_CERT environment variable)"),
                            type=from_environ("RHSM_CERT"))
        group.add_argument("--rhsm-key",
                           help=("RHSM API key path",
                                 "(or set RHSM_KEY environment variable)"),
                           type=from_environ("RHSM_KEY"))

    @property
    def rhsm_client(self):
        """ RHSM client used for AMI related info on RHSM.

        Error will be raised if the URL is not provided in the CLI.
        """
        with self._lock:
            if not self._instance:
                self._instance = self._get_instance()
            return self._instance

    def _get_instance(self):
        rhsm_url = self._service_args.rhsm_url
        if not rhsm_url:
            raise Exception("RHSM URL not provided")

        cert = self._service_args.rhsm_cert, self._service_args.rhsm_key
        return RHSMClient(rhsm_url, cert=cert)
    