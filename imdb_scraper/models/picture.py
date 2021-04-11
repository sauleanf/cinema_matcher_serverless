from models.director import Director

GENRES = [
    "adult",
    "action",
    "adventure",
    "animation",
    "comedy",
    "crime",
    "documentary",
    "drama",
    "fantasy",
    "horror",
    "mystery",
    "romance",
    "scifi",
    "short",
    "sport",
    "superhero",
    "thriller"
]


class Picture:
    FIELDS = [
                'name',
                'description',
                'released_at',
                'rating',
                'length',
                'image',
                *GENRES,
                'directors'
            ]

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', None)
        self.description = kwargs.get('description', None)
        self.released_at = kwargs.get('released_at', None)
        self.rating = kwargs.get('released_at', 0)
        self.image = kwargs.get('image', None)
        self.length = kwargs.get('length', 0)
        self.directors = kwargs.get('directors', [])
        self.genres = kwargs.get('genres', [])

    def add_director(self, director_name):
        director = Director()
        director.fullname = director_name
        self.directors.append(director)

    def __iter__(self):
        picture_iter = [
            self.name,
            self.description,
            self.released_at,
            self.rating,
            self.length,
            self.image,
        ]

        for genre in GENRES:
            if genre in self.genres:
                picture_iter.append(True)
            else:
                picture_iter.append(False)

        for director in self.directors:
            picture_iter.append(director.fullname)

        yield from picture_iter
