# recommendations/constants.py

GENRE_CHOICES = [
    ('', '---------'),  # Default empty option
    ('Action', 'Action'),
    ('Adventure', 'Adventure'),
    ('Animation', 'Animation'),
    ('Children', 'Children'),
    ('Comedy', 'Comedy'),
    ('Crime', 'Crime'),
    ('Documentary', 'Documentary'),
    ('Drama', 'Drama'),
    ('Fantasy', 'Fantasy'),
    ('Film-Noir', 'Film-Noir'),
    ('Horror', 'Horror'),
    ('IMAX', 'IMAX'),
    ('Musical', 'Musical'),
    ('Mystery', 'Mystery'),
    ('Romance', 'Romance'),
    ('Sci-Fi', 'Sci-Fi'),
    ('Thriller', 'Thriller'),
    ('War', 'War'),
    ('Western', 'Western'),
]

# List of just the genre names (no empty option)
GENRES = [choice[0] for choice in GENRE_CHOICES[1:]]