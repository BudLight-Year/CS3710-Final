import os
import numpy as np
import pandas as pd
import tensorflow as tf
from recommendations.models import EnhancedRecommender, Movie


GENRE_CHOICES = [
    'Action', 'Adventure', 'Animation', 'Children', 'Comedy',
    'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir',
    'Horror', 'IMAX', 'Musical', 'Mystery', 'Romance', 'Sci-Fi',
    'Thriller', 'War', 'Western'
]


def load_model():
    print("Starting model loading process...")

    try:
        movies_data = pd.DataFrame(
            list(Movie.objects.values('movie_id', 'title', 'genres', 'mean', 'count', 'year'))
        )

        genres_list = movies_data['genres'].str.get_dummies(sep='|')

        for genre in GENRE_CHOICES:
            if genre not in genres_list.columns:
                genres_list[genre] = 0

        movies_data = pd.concat([
            movies_data,
            genres_list[GENRE_CHOICES].astype(np.float32)
        ], axis=1)

        movies_data['year_normalized'] = (movies_data['year'] - movies_data['year'].min()) / (
            movies_data['year'].max() - movies_data['year'].min())

        max_ratings = movies_data['count'].max()
        movies_data['popularity'] = (
            0.3 * movies_data['count'].div(max_ratings) +
            0.7 * movies_data['mean'].div(5.0)
        ).astype(np.float32)

        base_dir = os.path.dirname(__file__)
        model = tf.keras.models.load_model(
            os.path.join(base_dir, 'movie_recommender.keras'),
            custom_objects={'EnhancedRecommender': EnhancedRecommender},
            compile=False
        )
        print("Model loaded successfully!")
        print("Model architecture:")
        model.summary()

        return model, movies_data

    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None


def prepare_genre_preferences(preference):
    """Convert Preference model data to model input format"""
    genre_preferences = np.zeros(len(GENRE_CHOICES), dtype=np.float32)
    
    # Get selected genres from Preference model fields
    selected_genres = [
        preference.genre1,
        preference.genre2,
        preference.genre3,
        preference.genre4,
        preference.genre5
    ]
    
    # Remove empty/None values
    selected_genres = [g for g in selected_genres if g]
    
    # Set selected genres to 1
    for genre in selected_genres:
        if genre in GENRE_CHOICES:
            idx = GENRE_CHOICES.index(genre)
            genre_preferences[idx] = 1
    
    # If not including other genres, set unselected to -1
    if not preference.include_other_genres:
        genre_preferences = np.where(genre_preferences == 0, -1, genre_preferences)
    
    return genre_preferences

def get_recommendations(model, movies_df, genre_preferences, top_k=10):
    """Get recommendations matching test script implementation with added randomization"""
    print("Starting recommendation generation...")
    
    # Convert 1's to selected genres list
    selected_genres = [
        genre for i, genre in enumerate(GENRE_CHOICES) 
        if genre_preferences[i] == 1
    ]
    print(f"Selected genres: {selected_genres}")
    
    # Convert -1's to excluded genres list
    excluded_genres = [
        genre for i, genre in enumerate(GENRE_CHOICES) 
        if genre_preferences[i] == -1
    ]
    if excluded_genres:
        print(f"Excluding movies with genres: {excluded_genres}")
    
    # Filter out movies with excluded genres
    filtered_df = movies_df.copy()
    if excluded_genres:
        exclude_mask = ~filtered_df[excluded_genres].any(axis=1)
        filtered_df = filtered_df[exclude_mask]
        print(f"Filtered from {len(movies_df)} to {len(filtered_df)} movies after excluding genres")
    
    # Filter for minimum ratings
    filtered_df = filtered_df[filtered_df['count'] >= 50]
    
    if len(filtered_df) == 0:
        print("No movies match the criteria!")
        return None
    
    batch_size = 1000
    all_scores = []
    
    for i in range(0, len(filtered_df), batch_size):
        batch_df = filtered_df.iloc[i:i+batch_size]
        
        batch_inputs = {
            'user_preferences': tf.constant(np.repeat([genre_preferences], len(batch_df), axis=0), dtype=tf.float32),
            'movie_genres': tf.constant(batch_df[GENRE_CHOICES].values, dtype=tf.float32),
            'year': tf.constant(batch_df[['year_normalized']].values, dtype=tf.float32),
            'rating': tf.constant(batch_df[['mean']].values / 5.0, dtype=tf.float32),
            'popularity': tf.constant(batch_df[['popularity']].values, dtype=tf.float32)
        }
        
        batch_scores = model(batch_inputs, training=False).numpy().flatten()
        all_scores.extend(batch_scores)
    
    scores = np.array(all_scores)
    
    # Normalize initial scores
    scores = (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
    
    # Calculate weighted ratings
    filtered_df['weighted_rating'] = filtered_df['mean'] * \
        np.log1p(filtered_df['count']) / np.log1p(filtered_df['count'].max())
    
    # Randomization 1: Add noise to model scores during combination
    noise_mult = np.random.uniform(0.9, 1.1, size=scores.shape) # adjust uniform range to adjust randomness
    scores = 0.7 * scores * noise_mult + 0.3 * filtered_df['weighted_rating'].values
    
    # Randomization 2: Add gaussian noise to final scores
    noise_add = np.random.normal(0, 0.05, size=scores.shape)  # 0.05 standard deviation for moderate randomness
    scores = scores + noise_add
    
    # Randomization 3: Get more candidates than needed and sample
    top_k_multiplier = 3  # Get 3x the movies we need
    candidate_count = min(top_k * top_k_multiplier, len(scores))
    top_indices = np.argsort(scores)[-candidate_count:][::-1]
    top_indices = np.random.choice(top_indices, size=min(top_k, len(top_indices)), replace=False)
    
    recommendations = filtered_df.iloc[top_indices].copy()
    recommendations['match_score'] = scores[top_indices]
    recommendations['matched_genres'] = recommendations.apply(
        lambda x: [g for g in selected_genres if x[g] == 1],
        axis=1
    )
    
    print("\nExample top recommendations:")
    for _, movie in recommendations.head(3).iterrows():
        print(f"{movie['title']}")
        print(f"Rating: {movie['mean']:.1f} ({movie['count']} ratings)")
        print(f"Genres: {movie['genres']}")
        print(f"Match score: {movie['match_score']:.3f}\n")
    
    return recommendations[['movie_id', 'match_score']]
