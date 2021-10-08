import os
import re
import shutil
import pytest
import logging
import json
from mock import patch, MagicMock
from pubtools._ami.tasks.push import AmiPush, entry_point


@pytest.fixture()
def stage_ami():
    path = "/tmp/aws_staged/region-1-hourly/AWS_IMAGES"
    if os.path.exists("/tmp/aws_staged"):
        shutil.rmtree("/tmp/aws_staged")
    os.makedirs("/tmp/aws_staged/region-1-hourly/AWS_IMAGES", mode=0755)
    open(os.path.join(path,"ami-1.raw"), 'a').close()

    j_file = os.path.join(os.path.dirname(__file__), "data/aws_staged/pub-mapfile.json")
    with open(j_file, 'r') as in_file:
        with open("/tmp/aws_staged/pub-mapfile.json", 'w') as out_file:
            data = json.load(in_file)
            json.dump(data, out_file)
    yield

    if os.path.exists("/tmp/aws_staged"):
        shutil.rmtree("/tmp/aws_staged")


@pytest.fixture(autouse=True)
def mock_aws_publish():
    with patch("pubtools._ami.services.aws.AWSService.publish") as m:
        yield m

"""
class FakeAmiPush(AmiPush):
    def __init__(self, *args, **kwargs):
        super(FakeAmiPush, self).__init__(*args, **kwargs)
"""     


def test_do_push(command_tester, requests_mocker, mock_aws_publish, stage_ami):
    requests_mocker.register_uri('GET', re.compile("amazon/provider_image_groups"),
    json={"body":[{"name": "RHEL_HOURLY", "providerShortName": "awstest"},]})
    requests_mocker.register_uri('POST', re.compile("amazon/region"))
    requests_mocker.register_uri('PUT', re.compile("amazon/amis"), status_code=500)
    requests_mocker.register_uri('POST', re.compile("amazon/amis"))
    publish_rv = MagicMock(id='ami-1234567')
    publish_rv.name = "ami-rhel"
    mock_aws_publish.return_value = publish_rv
    #aws_staged = os.path.join(os.path.dirname(__file__), "data/aws_staged")
    aws_staged = "/tmp/aws_staged"

    command_tester.test(
        lambda: entry_point(AmiPush),
        [
            "test-push",
            "--source",
            aws_staged,
            "--rhsm-url",
            "https://example.com",
            "--aws-provider-name",
            "awstest",
            "--retry-wait",
            "1",
            "--aws-access-id",
            "access_id",
            "--aws-secret-key",
            "secret_key",
            "--ship"

        ]
    )
