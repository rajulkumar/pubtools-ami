import os
import re
import shutil
import pytest
import json
from mock import patch, MagicMock
from pubtools._ami.tasks.push import AmiPush, entry_point

AMI_STAGE_ROOT = "/tmp/aws_staged"

@pytest.fixture(scope="session", autouse=True)
def stage_ami():
    if os.path.exists(AMI_STAGE_ROOT):
        shutil.rmtree(AMI_STAGE_ROOT)
    ami_dest = os.path.join(AMI_STAGE_ROOT, "region-1-hourly/AWS_IMAGES")
    os.makedirs(ami_dest, mode=0755)
    open(os.path.join(ami_dest, "ami-1.raw"), 'a').close()

    j_file = os.path.join(os.path.dirname(__file__), "data/aws_staged/pub-mapfile.json")
    with open(j_file, 'r') as in_file:
        with open(os.path.join(AMI_STAGE_ROOT, "pub-mapfile.json"), 'w') as out_file:
            data = json.load(in_file)
            json.dump(data, out_file)
    yield

    if os.path.exists(AMI_STAGE_ROOT):
        shutil.rmtree(AMI_STAGE_ROOT)


@pytest.fixture(autouse=True)
def mock_aws_publish():
    with patch("pubtools._ami.services.aws.AWSService.publish") as m:
        publish_rv = MagicMock(id='ami-1234567')
        publish_rv.name = "ami-rhel"
        m.return_value = publish_rv
        yield m

@pytest.fixture(autouse=True)
def mock_rhsm_api(requests_mocker):
    requests_mocker.register_uri('GET', re.compile("amazon/provider_image_groups"),
    json={"body":[{"name": "RHEL_HOURLY", "providerShortName": "awstest"},]})
    requests_mocker.register_uri('POST', re.compile("amazon/region"))
    requests_mocker.register_uri('PUT', re.compile("amazon/amis"))
    requests_mocker.register_uri('POST', re.compile("amazon/amis"))


def test_do_push(command_tester, requests_mocker, mock_aws_publish):
    requests_mocker.register_uri('PUT', re.compile("amazon/amis"), status_code=500)

    command_tester.test(
        lambda: entry_point(AmiPush),
        [
            "test-push",
            "--source",
            AMI_STAGE_ROOT,
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
