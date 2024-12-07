import pandas as pd
import os
import requests
from django.core.management.base import BaseCommand
from recommendations.models import Movie
from django.db import transaction

class Command(BaseCommand):
    help = 'Import movies from movies.csv and ratings.csv files'

    def add_arguments(self, parser):
        # Make arguments optional since we might use URLs instead
        parser.add_argument('--movies_csv_path', type=str, help='The path to the movies CSV file', required=False)
        parser.add_argument('--ratings_csv_path', type=str, help='The path to the ratings CSV file', required=False)

    def handle(self, *args, **kwargs):
        # Get URLs from environment variables
        movies_url = os.getenv('MOVIES_CSV_URL')
        ratings_url = os.getenv('RATINGS_CSV_URL')
        
        if movies_url and ratings_url:
            self.stdout.write('Downloading CSV files from Google Drive...')
            try:
                # Download movies CSV
                movies_response = requests.get(movies_url)
                movies_response.raise_for_status()
                movies_df = pd.read_csv(pd.io.common.StringIO(movies_response.text))
                
                # Download ratings CSV
                ratings_response = requests.get(ratings_url)
                ratings_response.raise_for_status()
                ratings_df = pd.read_csv(pd.io.common.StringIO(ratings_response.text))
                
                self.stdout.write('Successfully downloaded CSV files')
                # Process the downloaded dataframes
                self.process_data(movies_df, ratings_df)
                
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'Error downloading CSV files: {str(e)}'))
                return
            except pd.errors.EmptyDataError:
                self.stdout.write(self.style.ERROR('Downloaded CSV files are empty'))
                return
        else:
            # Use local files if URLs not provided
            movies_csv_path = kwargs.get('movies_csv_path')
            ratings_csv_path = kwargs.get('ratings_csv_path')
            
            if not movies_csv_path or not ratings_csv_path:
                raise ValueError(
                    "Either provide both CSV paths or set MOVIES_CSV_URL and RATINGS_CSV_URL environment variables"
                )
            
            try:
                self.stdout.write('Reading local CSV files...')
                movies_df = pd.read_csv(movies_csv_path)
                ratings_df = pd.read_csv(ratings_csv_path)
                self.process_data(movies_df, ratings_df)
            except FileNotFoundError as e:
                self.stdout.write(self.style.ERROR(f'Error reading CSV files: {str(e)}'))
                return
            except pd.errors.EmptyDataError:
                self.stdout.write(self.style.ERROR('CSV files are empty'))
                return

    def process_data(self, movies_df, ratings_df):
        self.stdout.write('Processing data...')
        
        # Extract year from title
        self.stdout.write('Extracting years from titles...')
        movies_df['year'] = pd.to_numeric(
            movies_df['title'].str.extract(r'\((\d{4})\)', expand=False),
            errors='coerce'
        )
        
        # Fill missing years with median
        median_year = int(movies_df['year'].median())
        movies_df['year'] = movies_df['year'].fillna(median_year).astype(int)
        
        self.stdout.write(f'Year range: {movies_df["year"].min()} to {movies_df["year"].max()}')
        self.stdout.write(f'Median year: {median_year}')
        
        # Print ratings information
        self.stdout.write('\nRatings Dataset Information:')
        self.stdout.write(f"Total number of ratings: {len(ratings_df):,}")
        self.stdout.write(f"Number of unique users: {ratings_df['userId'].nunique():,}")
        self.stdout.write(f"Number of unique movies rated: {ratings_df['movieId'].nunique():,}")
        
        # Verify ratings distribution
        self.stdout.write('\nRatings Distribution:')
        ratings_dist = ratings_df['rating'].value_counts().sort_index()
        for rating, count in ratings_dist.items():
            self.stdout.write(f"Rating {rating}: {count:,} ratings ({(count/len(ratings_df)*100):.2f}%)")
        
        # Calculate mean rating and count for each movie
        self.stdout.write('\nCalculating rating statistics...')
        rating_stats = ratings_df.groupby('movieId').agg({
            'rating': ['mean', 'count']
        }).reset_index()
        
        # Flatten multi-level columns
        rating_stats.columns = ['movieId', 'mean_rating', 'rating_count']
        
        # Verify total ratings matches
        total_ratings_check = rating_stats['rating_count'].sum()
        self.stdout.write(f"\nVerification - Total ratings from aggregation: {total_ratings_check:,}")
        if total_ratings_check != len(ratings_df):
            self.stdout.write(self.style.WARNING(
                f"Warning: Rating count mismatch! Original: {len(ratings_df):,}, "
                f"Aggregated: {total_ratings_check:,}"
            ))
        
        # Merge movies with rating stats
        movies_df = pd.merge(
            movies_df,
            rating_stats,
            on='movieId',
            how='left'
        )
        
        # Check for any movies that had ratings but weren't in movies_df
        rated_movies_not_in_db = set(ratings_df['movieId']) - set(movies_df['movieId'])
        if rated_movies_not_in_db:
            self.stdout.write(self.style.WARNING(
                f"\nWarning: Found {len(rated_movies_not_in_db)} movies with ratings "
                f"but no movie data"
            ))
        
        # Fill NaN values for movies with no ratings
        movies_df['mean_rating'] = movies_df['mean_rating'].fillna(0.0)
        movies_df['rating_count'] = movies_df['rating_count'].fillna(0)
        
        self.stdout.write(f'\nProcessing {len(movies_df):,} movies...')
        
        # Convert DataFrame to list of Movie instances
        movies_list = [
            Movie(
                movie_id=row['movieId'],
                title=row['title'],
                genres=row['genres'],
                mean=float(row['mean_rating']),
                count=int(row['rating_count']),
                year=int(row['year'])
            )
            for index, row in movies_df.iterrows()
        ]
        
        # Bulk create all Movie instances within a transaction
        with transaction.atomic():
            # Clear existing movies if any
            Movie.objects.all().delete()
            # Create new movies
            Movie.objects.bulk_create(movies_list)
        
        # Print detailed statistics
        self.stdout.write('\nFinal Dataset Statistics:')
        self.stdout.write(f"Total movies: {len(movies_df):,}")
        self.stdout.write(f"Movies with ratings: {len(movies_df[movies_df['rating_count'] > 0]):,}")
        self.stdout.write(f"Average rating: {movies_df['mean_rating'].mean():.2f}")
        self.stdout.write(f"Average number of ratings: {movies_df['rating_count'].mean():.2f}")
        self.stdout.write('\nYear Statistics:')
        self.stdout.write(f"Earliest year: {movies_df['year'].min()}")
        self.stdout.write(f"Latest year: {movies_df['year'].max()}")
        self.stdout.write(f"Most common year: {movies_df['year'].mode().iloc[0]}")
        
        # Get top 5 most rated movies
        top_rated = movies_df.nlargest(5, 'rating_count')
        self.stdout.write('\nTop 5 Most Rated Movies:')
        for _, movie in top_rated.iterrows():
            self.stdout.write(
                f"{movie['title']} ({movie['year']}): {int(movie['rating_count']):,} ratings "
                f"(avg rating: {movie['mean_rating']:.2f})"
            )
            
        # Get distribution of ratings
        self.stdout.write('\nRating Count Distribution:')
        percentiles = [0, 25, 50, 75, 90, 95, 99, 100]
        for p in percentiles:
            count = movies_df['rating_count'].quantile(p/100)
            self.stdout.write(f"{p}th percentile: {int(count):,} ratings")

        self.stdout.write(self.style.SUCCESS('\nImport completed successfully'))

        