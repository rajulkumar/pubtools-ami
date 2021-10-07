import threading
import os
import logging
from datetime import datetime

import requests
from more_executors import Executors
from more_executors.futures import f_map

LOG = logging.getLogger("pubtools.ami")


class RHSMClient(object):
    # Client for RHSM updates.

    _REQUEST_THREADS = int(os.environ.get("RHSM_REQUEST_THREADS", "4"))

    def __init__(self, url, max_retry_sleep=None, **kwargs):
        """Create a new RHSM client.

        Arguments:
            ulr(str)
                Base URL of the RHSM API.
            max_retry_sleep (float)
                Max number of seconds to sleep between retries.
                Mainly provided so that tests can reduce the time needed to retry.
            kwargs
                Remaining arguments are used to initialize the requests.Session()
                used within this class (e.g. "verify", "auth").
        """
        self._url = url
        self._tls = threading.local()

        retry_args = {}
        if max_retry_sleep:
            retry_args["max_sleep"] = max_retry_sleep

        self._session_attrs = kwargs
        self._executor = (
            Executors.thread_pool(name="rhsm-client", max_workers=self._REQUEST_THREADS)
            #.with_map(self._check_http_response)
            .with_retry(**retry_args)
        )

    @staticmethod
    def _check_http_response(response):
        # TODO: process response
        response.raise_for_status()

    @property
    def _session(self):
        if not hasattr(self._tls, "session"):
            self._tls.session = requests.Session()
            for (key, value) in self._session_attrs.items():
                setattr(self._tls.session, key, value)
        return self._tls.session

    # TODO: reduce this to _verb
    def _get(self, *args, **kwargs):
        return self._session.get(*args, **kwargs)

    def _send(self, *args, **kwargs):
        return self._session.send(*args, **kwargs)

    def rhsm_products(self):
        url = os.path.join(self._url,
                           "/v1/internal/cloud_access_providers/amazon" +
                           "/provider_image_groups")

        def _on_failure(exception):
            LOG.error("Unable to get RHSM products: %s", exception)
            raise exception

        out = self._executor.submit(self._get, url)

        out = f_map(out, fn=self._check_http_response, error_fn=_on_failure)

        return out

    def create_region(self, image_id, region, aws_provider_name):
        url = os.path.join(self._url,
                           "v1/internal/cloud_access_providers/amazon/regions")

        def _on_failure(exception):
            LOG.error("Failed creating region %s for image %s: %s",
                      region, image_id, exception)
            raise exception

        rhsm_region = {"regionID": region,
                       "providerShortname": aws_provider_name}
        req = requests.Request("POST", url, json=rhsm_region)
        prepped_req = self._session.prepare_request(req)

        out = self._executor.submit(self._send, prepped_req)
        out = f_map(out, error_fn=_on_failure)

        return out

    def update_image(self, image_id, image_name, arch, product_name,
                     version=None, variant=None):
        url = os.path.join(self._url, "/v1/internal/cloud_access_providers/amazon/amis")

        def _on_failure(exception):
            LOG.error("Failed to update image %s with exception %s", image_id, exception)
        """
        def _on_response(response):
            if not response.ok:
                LOG.warning("Update to RHSM failed for %s with error code %s. " \
                            "Image might not be present on RHSM for update.",
                            image_id, response.status_code)
            return response
        """
        now = datetime.utcnow().replace(microsecond=0).isoformat()
        rhsm_image = {"amiID": image_id,
                      "arch": arch.lower(),
                      "product": product_name,
                      "version": version,
                      "variant": variant,
                      "description": "Released %s on %s" % (image_name, now),
                      "status": "VISIBLE"
                     }
        req = requests.Request("PUT", url, json=rhsm_image)
        prepped_req = self._session.prepare_request(req)

        out = self._executor.submit(self._send, prepped_req)
        #out = f_map(out, fn=_on_response, error_fn=_on_failure)
        out = f_map(out, error_fn=_on_failure)
        return out

    def create_image(self, image_id, image_name, arch, product_name,
                     region, version=None, variant=None):
        url = os.path.join(self._url, "/v1/internal/cloud_access_providers/amazon/amis")

        def _on_failure(exception):
            LOG.error("Failed to update image %s with exception %s", image_id, exception)

        now = datetime.utcnow().replace(microsecond=0).isoformat()
        rhsm_image = {"amiID": image_id,
                      "region": region,
                      "arch": arch.lower(),
                      "product": product_name,
                      "version": version,
                      "variant": variant,
                      "description": "Released %s on %s" % (image_name, now),
                      "status": "VISIBLE"
                     }
        req = requests.Request("POST", url, json=rhsm_image)
        prepped_req = self._session.prepare_request(req)

        out = self._executor.submit(self._send, prepped_req)
        out = f_map(out, error_fn=_on_failure)

        return out
