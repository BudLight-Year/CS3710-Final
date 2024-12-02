# MLWebApp

## Table of Contents
1. Introduction
2. Setup
3. Setting Up the Database
4. Running the Server
5. Using the Web App

## Introduction

This project utilizes a Keras neural network movie recommender inside a Django web application.

The model was trained on the MovieLens 32M dataset at https://grouplens.org/datasets/movielens/32m.
Mainly data used was from movies.csv and ratings.csv.
Features used:
Movie features: movie_id, title, genres
rating features: user_id, rating, movie_id

The neural network has multiple subnetworks that each process things like genre matching and similarities, user preferences, and movie metadata. The final subnetwork combines all the previous networks to score movies on how well they are a match for the user based on their preferences.

Since ratings data would be too much storage for the webapp a collaborative filter didnt work, as the approach i used would dynamically use all the ratings data(all 32 million entries). So it is not present in this version.

The front end for the machine learning model can be found in MLWebApp/recommendations/views.py.
The functionality of the machine learning model can be fund in MLWebApp/recommendations/utils.py.
The Machine learning model class definition can be found in MLWebApp/recommendations/models.py, at the bottom of the file.

## Setup

1. **Ensure you have Python installed on your machine**.
2. **Create a virtual environment**.
3. **Activate your virtual environment**.
4. **Install all requirements**:

    ```sh
    pip3 install -r requirements.txt
    ```

5. **Download the MovieLens 32M dataset** from [here](https://grouplens.org/datasets/movielens/32m/).
6. **Place `movies.csv` and `ratings.csv` inside the `MLWebApp` directory**. Ensure they are in `MLWebApp`, *not* `MLWebApp/MLWebApp`.

## Setting Up the Database

1. **Run management commands to setup the database**:

    ```sh
    python manage.py makemigrations
    python manage.py migrate
    ```

    This will create the database for the web app.

2. **Populate the database with the data from `movies.csv` and `ratings.csv`**:

    ```sh
    python manage.py import_movies movies.csv ratings.csv
    ```

    This will do some data preprocessing and add the data to the Movies table in the database.

## Running the Server

1. **Run the server**:

    ```sh
    python manage.py runserver
    ```

2. **Access the website** on [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Using the Web App

### Sign Up

1. **Click "Sign Up"** at the right of the navbar at the top of the page.
2. **Enter email, username, and a password**.

    The site currently doesn't check for valid email addresses, so feel free to use an email such as `test@test.com`.

### Get a New Recommendation

1. **Click "New Recommendation"** on the navbar.
2. **Enter 1-5 genres**.
3. **Select or unselect the checkbox** to include other genres.
4. **Submit the form**. Your form input will be fed to the machine learning model, and it will generate a recommendation.
5. **View the recommendation**. You will be redirected to the recommendation output page where you can see the movies selected as recommendations and some extra information about the movies.
6. **Provide feedback** at the bottom of the page by determining if the recommendation was good or not.

### View All Recommendations

1. **Click "All Recommendations"** in the navbar.
2. **View all recommendations** labeled by the date the recommendation was generated and the preferences used.
