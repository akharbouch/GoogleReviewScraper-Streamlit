import streamlit as st
from openai import OpenAI

from serpapi import GoogleSearch
import googlemaps
import csv
import pandas as pd
from tqdm.notebook import tqdm
tqdm.pandas()


serp_api_key=st.secrets["api"]["serp_api_key"]
def search_results(google_search):
    params = {
      "engine": "google",
      "q": google_search,
      "api_key": serp_api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    return results

def store_search_id(results):  
    try: 
        return results['search_metadata']['id']
    except:
        return "No searchID generated"

def get_place_id(results):  
    try: 
        return results['knowledge_graph']['place_id']
    except:
        return "No place found"

def get_place_address(results):
    try:
        return results['knowledge_graph']['address']
    except:
        return "No place found"

def get_shop_name(results):
    try: 
        return results['knowledge_graph']['title']
    except:
        return "No place found"

def get_search_link(results):
    try: 
        return results['knowledge_graph']['knowledge_graph_search_link']
    except:
        return "No place found"

def price_lookup(results):
    try:
        return results['knowledge_graph']['price']
    except:
        return "No price found"

def googleclassification_lookup(results):
    try:
        return results['knowledge_graph']['type']
    except:
        return "No Google Classification found"
    
def reservation_type(results):
    try:
        return results['knowledge_graph']['reservation_providers'][0]['name']
    except:
        return "No reservation provider found"

def email_lookup(results):
    try:
        email1=results['organic_results'][0]['snippet_highlighted_words']
    except:
        email1="No email found"
    try:
        email2=results['organic_results'][1]['snippet_highlighted_words']
    except:
        email2="No email found"
    try:
        return email1,email2 
    except:
        return "No email found"


# Return how many reviews mention pizza or alcohol
def review_audit(place_id,max_reviews):

    reviews = fetch_reviews(place_id, serp_api_key, max_reviews)


    review_count=0
    reviews_with_pizza=0
    reviews_with_alcohol = 0
    pizza_keywords = ['pizza', 'pie', 'pizzeria', 'slice']
    alcohol_keywords = ['liquor', 'whisky', 'cocktail', 'wine', 'alcohol',' gin ', 'tequila', 'scotch', 'bourbon']
    for review in reviews:
        try:
            if len(review['snippet']) > 1:
                review_count += 1

                if any(keyword in review['snippet'].lower() for keyword in pizza_keywords):
                    reviews_with_pizza += 1
                
                if any(keyword in review['snippet'].lower() for keyword in alcohol_keywords):
                    reviews_with_alcohol += 1
        except:
            review_count += 0
    return [review_count, reviews_with_pizza, reviews_with_alcohol]
    
# Return all reviews from Review API (paid API that requires 2 pings in order to get 18 results - each review page is a ping)
def fetch_reviews(place_id, api_key, max_reviews=18):
    all_reviews = []
    next_page_token = None
    if place_id is None:
        return "No Place_ID provided or Place_ID is None"
    while len(all_reviews) < max_reviews:
        params = {
            "engine": "google_maps_reviews",
            "place_id": place_id,
            "api_key": api_key,
            "hl": "en",  
            "sort_by": "qualityScore"
        }

        if next_page_token:
            params["next_page_token"] = next_page_token

        search = GoogleSearch(params)
        results = search.get_dict()

        if "reviews" in results:
            all_reviews.extend(results["reviews"])

        if "serpapi_pagination" in results and "next_page_token" in results["serpapi_pagination"]:
            next_page_token = results["serpapi_pagination"]["next_page_token"]
        else:
            break

    return all_reviews[:18]



# Show title and description.
st.title("Google Review Scraper")
st.write(
    "Please enter the Shop Name, Address, and Zip Code"

)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Let the user upload a file via `st.file_uploader`.
    uploaded_file = st.file_uploader(
        "Upload a document (.txt or .md)", type=("txt", "md")
    )

    # Ask the user for a question via `st.text_area`.
    question = st.text_area(
        "Now ask a question about the document!",
        placeholder="Can you give me a short summary?",
        disabled=not uploaded_file,
    )

    if uploaded_file and question:

        # Process the uploaded file and question.
        document = uploaded_file.read().decode()
        messages = [
            {
                "role": "user",
                "content": f"Here's a document: {document} \n\n---\n\n {question}",
            }
        ]

        # Generate an answer using the OpenAI API.
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
        )

        # Stream the response to the app using `st.write_stream`.
        st.write_stream(stream)
