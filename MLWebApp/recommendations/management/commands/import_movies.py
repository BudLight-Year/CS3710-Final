import pandas as pd
from django.core.management.base import BaseCommand
from recommendations.models import Movie

class Command(BaseCommand):
    help = 'Import movies from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file_path']
        self.import_movies_from_csv(csv_file_path)

    def import_movies_from_csv(self, csv_file_path):
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_file_path)

        # Convert DataFrame to list of Movie instances
        movies_list = [
            Movie(
                movie_id=row['movieId'],
                title=row['title'],
                genres=row['genres']
            )
            for index, row in df.iterrows()
        ]

        # Bulk insert all Movie instances
        Movie.objects.bulk_create(movies_list)
        self.stdout.write(self.style.SUCCESS('Successfully added all movies'))
