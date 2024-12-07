import pandas as pd
from django.core.management.base import BaseCommand
from recommendations.models import Movie
from django.db import transaction

class Command(BaseCommand):
    help = 'Batch insert movies from processed_movies.csv into the database'

    def handle(self, *args, **kwargs):
        # Path to the processed CSV file
        processed_csv_path = 'processed_movies.csv'

        try:
            # Read the processed CSV file
            self.stdout.write('Reading processed CSV file...')
            movies_df = pd.read_csv(processed_csv_path)
            self.stdout.write(f'Successfully read {len(movies_df):,} movies from CSV')

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
                for _, row in movies_df.iterrows()
            ]

            # Perform batch inserts within a transaction
            with transaction.atomic():
                # Clear existing movies if any
                self.stdout.write('Clearing existing movies...')
                Movie.objects.all().delete()
                
                # Batch insert new movies
                batch_size = 1000  # Adjust batch size as needed
                self.stdout.write('Inserting movies in batches...')
                for i in range(0, len(movies_list), batch_size):
                    batch = movies_list[i:i + batch_size]
                    Movie.objects.bulk_create(batch)
                    self.stdout.write(f'Inserted batch {i // batch_size + 1}')
                
                self.stdout.write(self.style.SUCCESS('Successfully imported movies into the database'))

        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f'Error reading processed CSV file: {str(e)}'))
        except pd.errors.EmptyDataError:
            self.stdout.write(self.style.ERROR('Processed CSV file is empty'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
