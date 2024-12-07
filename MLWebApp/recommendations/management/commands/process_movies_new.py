import pandas as pd
from django.core.management.base import BaseCommand
from recommendations.models import Movie
from django.db import transaction

class Command(BaseCommand):
    help = 'Batch insert movies from processed_movies.csv into the database'

    def handle(self, *args, **kwargs):
        # Path to the processed CSV file
        processed_csv_path = 'processed_movies.csv'
        chunk_size = 1000  # Adjust chunk size as needed

        try:
            self.stdout.write('Reading processed CSV file in chunks...')
            chunks = pd.read_csv(processed_csv_path, chunksize=chunk_size)

            for chunk in chunks:
                self.stdout.write(f'Processing chunk with {len(chunk):,} records...')
                self.process_chunk(chunk)

            self.stdout.write(self.style.SUCCESS('Successfully imported movies into the database'))

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f'Error reading processed CSV file: {str(e)}'))
        except pd.errors.EmptyDataError:
            self.stdout.write(self.style.ERROR('Processed CSV file is empty'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))

    def process_chunk(self, chunk):
        # Prepare a list of Movie instances for bulk creation
        movies_list = [
            Movie(
                movie_id=row['movieId'],
                title=row['title'],
                genres=row['genres'],
                mean=float(row['mean_rating']),
                count=int(row['rating_count']),
                year=int(row['year'])
            )
            for _, row in chunk.iterrows()
        ]

        # Perform batch inserts within a transaction
        with transaction.atomic():
            # Batch insert new movies
            batch_size = 1000  # Adjust batch size as needed
            for i in range(0, len(movies_list), batch_size):
                batch = movies_list[i:i + batch_size]
                Movie.objects.bulk_create(batch)
                self.stdout.write(f'Inserted batch with {len(batch):,} records')
