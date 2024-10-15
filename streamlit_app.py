import streamlit as st
from serpapi import GoogleSearch
import googlemaps
import csv
import pandas as pd
from tqdm.notebook import tqdm
import requests
tqdm.pandas()

import gspread
from google.oauth2.service_account import Credentials

serp_api_key=st.secrets["serp_api_key"]
def search_results(google_search):
    params = {
      "engine": "google",
      "q": google_search,
      "api_key": serp_api_key,
      "hl":"en",
      "gl":"us", 
      "device":"desktop"
    }

    search = GoogleSearch(params)  # Unpacking params
    results = search.get_dict()  # Assuming this method exists
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

# Load Google service account credentials from Streamlit secrets
creds_dict = st.secrets["gcp_service_account"]

# Define the scope for Google Sheets API (make sure this scope is correct)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Initialize the credentials with the correct scope
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

# Authorize the client with the credentials
client = gspread.authorize(creds)

# Show title and description.
st.title("Google Review Scraper")


# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
query = st.text_input("Please enter the Shop Name, Address, and Zip Code", type="default")
clicked=st.button("Submit query")

if clicked==False:
    st.info("**Example**: *Portofino's Italian Kitchen 396 Brockton Ave 02351*", icon="⌨️")

elif clicked and len(query)<10:
    st.error("Input too short",icon="🚨")
    st.info("Example: Portofino's Italian Kitchen 396 Brockton Ave 02351", icon="⌨️")
     
elif clicked:
    searchresults=search_results(query)
    placeid=get_place_id(searchresults)
    if placeid is None:
        error_message = "Could not find PlaceID on Google"
        st.error("Could not find PlaceID on Google",icon="🚨")
    else:
        address=get_place_address(searchresults)
        name=get_shop_name(searchresults)
        print(name)
        searchlink=get_search_link(searchresults)
        reviewsresult=review_audit(placeid,18)

        reservationprovider=reservation_type(searchresults)
        emails_found=email_lookup(searchresults)
        price_found=price_lookup(searchresults)
        googleclassification_found=googleclassification_lookup(searchresults)
        if reviewsresult[0]==0:
            st.error("No more search credits available or no reviews found. Run a manual Google Search for this shop to see if reviews exist and if so, it likely means we have no more search credits",icon="🚨")
        else:
            perc_pizza_reviews=reviewsresult[1]/reviewsresult[0]*100
            perc_alc_reviews=reviewsresult[2]/reviewsresult[0]*100
            # st.metric(label="The name of the shop is:", value=name)
            # st.metric(label="The address of the shop is:", value=address)
            # st.metric(label="The search URL of the shop is:", value=searchlink)
            st.write("**The name of the shop is:**")
            st.info(name)
            st.divider()
            st.write("**The address of the shop is:**")
            st.info(address)
            st.divider()
            st.write("**The search URL of the shop is:**")
            st.info(searchlink)
            st.divider()
            st.write("**The reservation provider is:**")
            st.info(reservationprovider)
            st.divider()
            st.write("**The Google Classification is:**")
            st.info(googleclassification_found)
            st.divider()
            st.write("**The Price Range is:**")
            st.info( price_found )
            st.divider()
            st.write("**Number of reviews scraped:**")
            st.info(reviewsresult[0])
            st.divider()
            st.write("**Number of reviews mentioning 'pizza':**")
            st.info(reviewsresult[1])
            st.divider()
            st.write("**The percentage of reviews mentioning 'pizza' is:**")
            st.info(f"{perc_pizza_reviews:.0f}%")
            st.divider()
            st.write("**The percentage of reviews mentioning 'alcohol' is:**")
            st.info(f"{perc_alc_reviews:.0f}%")

            # st.metric(label="Number of reviews scraped:", value=reviewsresult[0])
            # st.metric(label="Number of reviews mentioning 'pizza':", value=reviewsresult[1])
            # st.metric(label="The percentage of reviews mentioning 'pizza' is:", value=f"{perc_pizza_reviews:.0f}%")
            
            # st.metric(label="The percentage of reviews mentioning alcohol is:", value=f"{perc_alc_reviews:.0f}%")
            # st.metric(label="The reservation provider is:", value=reservationprovider)
            # st.metric(label="The Google Classification found is:", value=googleclassification_found)
            

            # The Google Form action URL
            form_url = 'https://docs.google.com/forms/d/e/1FAIpQLSfHCWhr8QXP7vAOP3WyJFSowu5BnMkm2QVrNKnwj7RTiN0sFg/formResponse'

            # The form fields (entry IDs) and the data to submit
            form_data = {
                'entry.196438386': query,
                'entry.217975455': address,
                'entry.315385946': reservationprovider,
                'entry.425258006': googleclassification_found,
                'entry.885294045': name,
                'entry.1147048836': price_found,
                'entry.1186099979': searchlink,
                'entry.1462800292': placeid,
                'entry.1507746828': reviewsresult[1],
                'entry.1765641676': reviewsresult[0],
                'entry.1808547668': reviewsresult[2]
            }

            # Submit the form using a POST request
            response = requests.post(form_url, data=form_data)

            # Check the response status
            if response.status_code == 200:
                st.divider()
                st.success("Data submitted to Google Sheets!")
            else:
                st.divider()
                st.error(f'Failed to submit to Google Sheets. Status code: {response.status_code}')






