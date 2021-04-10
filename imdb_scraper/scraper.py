from bs4 import BeautifulSoup
from imdb_scraper.models.picture import Picture
import boto3
import csv
import json
import requests
from datetime import datetime


IMDB_ROOT_URL = 'https://www.imdb.com'


def process_length(picture_soup):
    time_element = picture_soup.find('time')
    if time_element is None:
        return None
    length = time_element['datetime']
    return int(length.replace('PT', '').replace('M', ''))


class IMDB:
    def __init__(self, html, **kwargs):
        self.filename = kwargs.get('filename', 'imdb.csv')
        self.bucket = kwargs.get('bucket', False)
        self.main_soup = BeautifulSoup(html, "html.parser")
        self.object_name = None

        self.scrap()
        self.upload_to_s3()

    def scrap(self):
        with open(f'/tmp/{self.filename}', 'w+') as imdb_csv:
            writer = csv.writer(imdb_csv)
            writer.writerow(Picture.FIELDS)

            for row_element in self.main_soup.find(
                    'tbody',
                    class_='lister-list').find_all('tr'):

                title_element = row_element.find(
                    'td',
                    class_='titleColumn').find('a')

                picture_imdb_url = f'{IMDB_ROOT_URL}{title_element["href"]}'

                res = requests.get(picture_imdb_url)

                picture = self.process_picture_data(BeautifulSoup(res.text, "html.parser"))

                writer.writerow(list(picture))
                print(f"Wrote row for picture {picture.name}")
            print('Done writing to CSV')

    def process_picture_data(self, picture_soup):
        print("Processing tag now")

        tag_element = picture_soup.find('script',
                                        type='application/ld+json')

        picture_data = json.loads(str(tag_element.string))
        picture = Picture(
            name=picture_data['name'],
            rating=float(picture_data['aggregateRating']['ratingValue']),
            length=process_length(picture_soup),
            description=picture_data['description'],
            published_at=picture_data['datePublished'],
            image=picture_data['image']
        )

        if isinstance(picture_data['genre'], list):
            picture.genres = [genre.lower() for genre in picture_data['genre']]
        else:
            picture.genres = [picture_data['genre'].lower()]

        creator_data = picture_data.get('creator', None)
        if creator_data is not None:
            if isinstance(picture_data['creator'], dict):
                creator_data = picture_data['creator']
                if creator_data["@type"] == "Person":
                    picture.add_director(creator_data["name"])
            else:
                for creator_data in picture_data['creator']:
                    if creator_data["@type"] == "Person":
                        picture.add_director(creator_data["name"])

        return picture

    def upload_to_s3(self):
        self.object_name = f"{self.filename}-{datetime.now().isoformat()}"
        res = boto3.client('s3').upload_file(f'/tmp/{self.filename}',
                                             self.bucket,
                                             self.object_name)

        return res
