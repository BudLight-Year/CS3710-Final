# WebApp ML Model Documentation:


## How to implement a Machine Learning Movie Recommendation Model into a Web Application

**Define your model.** 
```python
class MovieGenreModel(tf.keras.Model):
    def __init__(self, movies, num_genres):
        super().__init__()
        
        self.movie_embedding = tf.keras.Sequential([
            tf.keras.layers.StringLookup(
                vocabulary=movies['movieId'].unique(),
                mask_token=None),
            tf.keras.layers.Embedding(
                input_dim=len(movies['movieId'].unique()) + 1,
                output_dim=32)
        ])
        
        self.genre_embedding = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32)
        ])
        
        self.rating_predictor = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1)
        ])

    def call(self, inputs):
        movie_emb = self.movie_embedding(inputs['movieId'])
        genre_emb = self.genre_embedding(inputs['genre_preferences'])
        combined = tf.concat([movie_emb, genre_emb], axis=1)
        return self.rating_predictor(combined)
```

**Preprocess data**
```python
    def load_and_preprocess_data():
    logger.info("Loading data...")
    movies = pd.read_csv('movies.csv')
    ratings = pd.read_csv('ratings.csv')
    
    movies['movieId'] = movies['movieId'].astype(str)
    movies['genres'] = movies['genres'].str.split('|')
    
    from sklearn.preprocessing import MultiLabelBinarizer
    mlb = MultiLabelBinarizer()
    genre_matrix = mlb.fit_transform(movies['genres'])
    genre_columns = mlb.classes_
    
    # Remove the "no genres" column if it exists
    if '(no genres listed)' in genre_columns:
        no_genres_idx = np.where(genre_columns == '(no genres listed)')[0][0]
        genre_matrix = np.delete(genre_matrix, no_genres_idx, axis=1)
        genre_columns = np.delete(genre_columns, no_genres_idx)
    
    genre_df = pd.DataFrame(genre_matrix, columns=genre_columns)
    movies = pd.concat([movies, genre_df], axis=1)
    
    ratings['movieId'] = ratings['movieId'].astype(str)
    movie_avg_ratings = ratings.groupby('movieId')['rating'].agg(['mean', 'count']).reset_index()
    movies = movies.merge(movie_avg_ratings, on='movieId', how='left')
    
    # Fill NaN values with 0
    movies['mean'] = movies['mean'].fillna(0)
    movies['count'] = movies['count'].fillna(0)
    
    # Verify that each movie has at least one genre
    genre_sums = genre_df.sum(axis=1)
    if (genre_sums == 0).any():
        logger.warning(f"Found {(genre_sums == 0).sum()} movies with no genres. These will be filtered out.")
        valid_movies = genre_sums > 0
        movies = movies[valid_movies].reset_index(drop=True)
    
    return movies, genre_columns
```


**Train and save the model**
```python
     # Create and train model
    model = MovieGenreModel(movies, len(genre_columns))
    
    # Create training dataset
    tf_dataset = tf.data.Dataset.from_tensor_slices((
        {
            'movieId': movies['movieId'].values,
            'genre_preferences': movies[genre_columns].values.astype(np.float32)
        },
        movies['mean'].values
    )).batch(128)
    
    model.compile(optimizer=tf.keras.optimizers.Adam(0.001),
                 loss=tf.keras.losses.MeanSquaredError())
    
    logger.info("Training model...")
    model.fit(tf_dataset, epochs=10)
    logger.info("Training complete")

    logger.info("Saving model...")
    model.save('genreModel.keras')
    logger.info("Model saved")
```


**Import Model into WebApp**

Saving the model will create a file, in the example above "genreModel.keras" will be the saved model.

To import the model simply copy the file into your webapp directory.

**Write the Machine Learning model class into the Web App to load the model into**

Simply copy and paste the model class definition into a models file in your webapp projec. Depending on the model you may need to add a decorator. 
For a keras model you will use:
```python
    @register_keras_serializable()
```
Additionally your model may need config functions to load the model functionality that was trained in. 
For the keras model:
```python
    def get_config(self):
        config = super().get_config()
        return config

    @classmethod
    def from_config(cls, config):
        return cls(**config)
```


**Create database models to store user input and model output**

For the MovieLens Dataset you can create a movie model to store the movies for the recommender to use.

```python
    class Movie(models.Model):
        movie_id = models.IntegerField(primary_key=True)
        title = models.CharField(max_length=255)
        genres = models.CharField(max_length=255)
        mean = models.FloatField(default=0)  # Average rating
        count = models.IntegerField(default=0)  # Number of ratings
        year = models.IntegerField(default=0)

        def __str__(self):
            return self.title

        def rounded_mean(self, decimals=2):
            """Return the average rating rounded to the specified number of decimal places."""
            return round(self.mean, decimals)
```

And you can use a Preference model to store user input
```python
    class Preference(models.Model):
        genre1 = models.CharField(max_length=255, blank=True, null=True)
        genre2 = models.CharField(max_length=255, blank=True, null=True)
        genre3 = models.CharField(max_length=255, blank=True, null=True)
        genre4 = models.CharField(max_length=255, blank=True, null=True)
        genre5 = models.CharField(max_length=255, blank=True, null=True)
        include_other_genres = models.BooleanField(default=True)
        
        def __str__(self):
            # Get all non-empty genres
            genres = [
                self.genre1, self.genre2, self.genre3, 
                self.genre4, self.genre5
            ]
            selected_genres = [g for g in genres if g]
            return f"Preference: {', '.join(selected_genres)}"
```
And to store recommendations:
```python
    class Recommendation(models.Model):
        user = models.ForeignKey('user.Myuser', on_delete=models.DO_NOTHING, related_name="recommendations")
        preference = models.ForeignKey('recommendations.Preference', on_delete=models.CASCADE, related_name="recommendation")
        movies = models.ManyToManyField(Movie, related_name="recommendations")
        date_created = models.DateTimeField(auto_now_add=True)


        def __str__(self): 
            return f"Recommendation for {self.user.username}"
```


**Take user input conducive to the input the model expects and save to input model**

Create a form to capture user input and save into the preference.
```python
    class PreferenceForm(forms.ModelForm):
        genre1 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
        genre2 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
        genre3 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
        genre4 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
        genre5 = forms.ChoiceField(choices=GENRE_CHOICES, required=False, initial='')
        include_other_genres = forms.BooleanField(
            required=False, 
            help_text="Include genres not listed above",
            initial=True
        )
        
        class Meta:
            model = Preference
            fields = ['genre1', 'genre2', 'genre3', 'genre4', 'genre5', 'include_other_genres']

        def clean(self):
            cleaned_data = super().clean()
            
            # Get all genre selections
            genres = [
                cleaned_data.get('genre1'),
                cleaned_data.get('genre2'),
                cleaned_data.get('genre3'),
                cleaned_data.get('genre4'),
                cleaned_data.get('genre5')
            ]
            
            # Check if at least one genre is selected (not empty)
            if not any(genre for genre in genres if genre):
                raise forms.ValidationError(
                    "Please select at least one genre in any of the fields.",
                    code='no_genre_selected'
                )
            
            return cleaned_data
```


**Give user input to the model to generate recommendations**
The most complicated part is creating functionality in your views to match functionality intended when training.

When the form is posted take the input and feed it to the ML model. 
```python
    def post(self, request):
        form = PreferenceForm(request.POST)
        if form.is_valid():
            preference = form.save(commit=False)
            genre_preferences = self.prepare_genre_preferences(preference)
            
            try:
                recommended_movies_df = self.get_recommendations(genre_preferences)
                
                if recommended_movies_df is None or len(recommended_movies_df) == 0:
                    form.add_error(None, "No movies found matching your criteria. Try different preferences.")
                    return render(request, 'recommendations/recommendation_engine.html', {'form': form})
```


**Save recommendations to output model**
At the end of the post method make sure you save all models in the database.
```python
                # Save preference
                preference.save()
                
                # Create recommendation
                recommendation = Recommendation.objects.create(
                    user=request.user,
                    preference=preference
                )
                
                # Get Movie objects and add to recommendation
                recommended_movies = Movie.objects.filter(
                    movie_id__in=recommended_movies_df['movie_id'].tolist()
                )
                recommendation.movies.add(*recommended_movies)
                
                return redirect('recommendations:recommendation_detail', recommendation_id=recommendation.id)
                
            except Exception as e:
                print(f"Error getting recommendations: {e}")
                import traceback
                traceback.print_exc()
                form.add_error(None, f"Error generating recommendations: {str(e)}")
                
        return render(request, 'recommendations/recommendation_engine.html', {'form': form})
```

**Create output view**
Now that we have the models we need in the database we can access them in a view/template so the user can see the results

```python
    class RecommendationDetailView(View):
        def get(self, request, recommendation_id):
            recommendation = get_object_or_404(Recommendation, id=recommendation_id)
            return render(request, 'recommendations/recommendation_detail.html', {
                'recommendation': recommendation,
            })
```












































