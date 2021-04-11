import json
from scraper import IMDB, IMDB_ROOT_URL
import requests


def lambda_handler(event, context):
    body = json.loads(event['body'])

    imdb_url = f'{IMDB_ROOT_URL}/chart/toptv/?ref_=nv_tvv_250'
    imdb_res = requests.get(imdb_url)
    scraper = IMDB(imdb_res.text, bucket=body.get('bucket'))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": f"Uploaded object {scraper.object_name} to bucket {scraper.bucket}"
        }),
    }
