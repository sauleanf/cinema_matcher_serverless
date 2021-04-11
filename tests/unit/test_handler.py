import pytest_path_hack # noqa
from datetime import datetime
from freezegun import freeze_time
import app
from moto import mock_s3
from unittest.mock import patch
import boto3
import filecmp
import json
import pytest
import os


FIXTURE_DIR = os.path.join('tests', 'unit', 'fixtures')


@pytest.fixture
def s3_bucket():
    return 'imdbmoviesfs'


@pytest.fixture
def apigw_event(s3_bucket):
    return {
        "body": json.dumps({'bucket': s3_bucket}),
        "resource": "/{proxy+}",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/{proxy+}",
            "httpMethod": "POST",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "identity": {
                "apiKey": "",
                "userArn": "",
                "cognitoAuthenticationType": "",
                "caller": "",
                "userAgent": "Custom User Agent String",
                "user": "",
                "cognitoIdentityPoolId": "",
                "cognitoIdentityId": "",
                "cognitoAuthenticationProvider": "",
                "sourceIp": "127.0.0.1",
                "accountId": "",
            },
            "stage": "prod",
        },
        "queryStringParameters": {"foo": "bar"},
        "headers": {
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "Accept-Language": "en-US,en;q=0.8",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Mobile-Viewer": "false",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "CloudFront-Viewer-Country": "US",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "X-Forwarded-Port": "443",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
            "X-Forwarded-Proto": "https",
            "X-Amz-Cf-Id": "aaaaaaaaaae3VYQb9jd-nvCd-de396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "CloudFront-Is-Tablet-Viewer": "false",
            "Cache-Control": "max-age=0",
            "User-Agent": "Custom User Agent String",
            "CloudFront-Forwarded-Proto": "https",
            "Accept-Encoding": "gzip, deflate, sdch",
        },
        "pathParameters": {"proxy": "/examplepath"},
        "httpMethod": "POST",
        "stageVariables": {"baz": "qux"},
        "path": "/examplepath",
    }


def mock_imdb_res(uri, *args, **kwargs):
    if uri == 'https://www.imdb.com/chart/toptv/?ref_=nv_tvv_250':
        html_filename = 'imdb.html'
    else:
        title_id = uri.split('/')[-2]
        html_filename = f'imdb_{title_id}.html'

    class MockedResponse:
        def __init__(self, _html_filename):
            self.html_filename = _html_filename

        @property
        def text(self):
            with open(self.html_filename) as html:
                return html.read()

    return MockedResponse(os.path.join(FIXTURE_DIR, html_filename))


@mock_s3
@patch('requests.get', side_effect=mock_imdb_res)
@freeze_time("2020-02-22")
def test_lambda_handler(freezer, apigw_event, s3_bucket):
    object_name = f"imdb.csv-{datetime.now().isoformat()}"
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket=s3_bucket)

    ret = app.lambda_handler(apigw_event, {})
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert data["message"] == f"Uploaded object {object_name} to bucket {s3_bucket}"

    expected_filename = os.path.join(FIXTURE_DIR, 'expected_imdb.csv')
    filename = os.path.join(FIXTURE_DIR, 'imdb.out.csv')

    s3.download_file(s3_bucket, object_name, filename)
    assert filecmp.cmp(expected_filename, filename)
