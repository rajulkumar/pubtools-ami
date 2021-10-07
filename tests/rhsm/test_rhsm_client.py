import logging
from mock import patch
from requests.exceptions import ConnectionError
from pubtools._ami.rhsm import RHSMClient

def test_rhsm_products(requests_mocker):
    url = "https://example.com/v1/internal/cloud_access_providers/amazon/provider_image_groups"
    products = {"body":[
                                       {"name": "RHEL", "providerShortName": "awstest"},
                                       {'name': 'RHEL_HOURLY', "providerShortName": "awstest"}
                                       ]}
    requests_mocker.register_uri("GET", url, [{"json":products},{"status_code": 500}])
    
    client = RHSMClient("https://example.com", cert=("client.crt", "client.key"))

    out = client.rhsm_products()
    out = out.result().json()
    assert out == products

    exception = client.rhsm_products().exception()
    assert "500 Server Error" in str(exception)
    
def test_create_region(requests_mocker):
    url = "https://example.com/v1/internal/cloud_access_providers/amazon/regions"
    m_create_region = requests_mocker.register_uri("POST", url, [{"status_code":200}, {"status_code": 500}])
    
    expected_region_req = {'regionID': 'us-east-1',
                                'providerShortname': 'AWS'}
    
    client = RHSMClient("https://example.com", cert=("client.crt", "client.key"))

    out = client.create_region("us-east-1", "AWS")
    assert out.result().ok
    assert m_create_region.call_count == 1
    assert m_create_region.last_request.json() == expected_region_req

    out = client.create_region("us-east-1", "AWS")
    assert not out.result().ok
    assert m_create_region.call_count == 2


def test_update_image(requests_mocker, caplog):
    url = "https://example.com/v1/internal/cloud_access_providers/amazon/amis"
    m_update_image = requests_mocker.register_uri("PUT", url, [{"status_code":200}, {"status_code": 500}, {"exc":ConnectionError}])
    caplog.set_level(logging.INFO)
    date_now = "2020-10-29T09:03:55"
    expected_update_img_req = {'status': 'VISIBLE',
                                  'amiID': 'ami-123',
                                  'product': 'RHEL',
                                  'description': 'Released ami-rhel on 2020-10-29T09:03:55',
                                  'variant': 'Server',
                                  'version': '7.3',
                                  'arch': 'x86_64',
                            }
    
    client = RHSMClient("https://example.com", cert=("client.crt", "client.key"), max_retry_sleep=0.001)
    with patch("pubtools._ami.rhsm.datetime") as now:
        now.utcnow().replace().isoformat.return_value = date_now
        out = client.update_image("ami-123", "ami-rhel", "x86_64", "RHEL", version="7.3", variant="Server")
    assert out.result().ok
    assert m_update_image.call_count == 1
    assert m_update_image.last_request.json() == expected_update_img_req

    out = client.update_image("ami-123", "ami-rhel", "x86_64", "RHEL", version="7.3", variant="Server")
    assert not out.result().ok
    assert m_update_image.call_count == 2

    out = client.update_image("ami-123", "ami-rhel", "x86_64", "RHEL", version="7.3", variant="Server")
    assert isinstance(out.exception(), ConnectionError)
    assert caplog.messages == ["Failed to process request to RHSM with exception "]
    
def test_create_image(requests_mocker, caplog):
    url = "https://example.com/v1/internal/cloud_access_providers/amazon/amis"
    m_create_image = requests_mocker.register_uri("POST", url, [{"status_code":200}, {"status_code": 500}, {"exc":ConnectionError}])
    caplog.set_level(logging.INFO)
    date_now = "2020-10-29T09:03:55"
    expected_create_img_req = {'status': 'VISIBLE',
                                  'amiID': 'ami-123',
                                  'product': 'RHEL',
                                  'description': 'Released ami-rhel on 2020-10-29T09:03:55',
                                  'arch': 'x86_64',
                                  'version': 'none',
                                  'variant': 'none',
                                  'region': 'us-east-1',
                            }
    
    client = RHSMClient("https://example.com", cert=("client.crt", "client.key"), max_retry_sleep=0.001)
    with patch("pubtools._ami.rhsm.datetime") as now:
        now.utcnow().replace().isoformat.return_value = date_now
        out = client.create_image("ami-123", "ami-rhel", "x86_64", "RHEL", "us-east-1")
    assert out.result().ok
    assert m_create_image.call_count == 1
    assert m_create_image.last_request.json() == expected_create_img_req

    out = client.create_image("ami-123", "ami-rhel", "x86_64", "RHEL", "us-east-1")
    assert not out.result().ok
    assert m_create_image.call_count == 2

    out = client.create_image("ami-123", "ami-rhel", "x86_64", "RHEL", "us-east-1")
    assert isinstance(out.exception(), ConnectionError)
    assert caplog.messages == ["Failed to process request to RHSM with exception "]