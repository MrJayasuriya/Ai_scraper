from apify_client import ApifyClient

# Initialize the ApifyClient with your API token
client = ApifyClient("apify_api_YngozeH7dWBGzFmzvITPYFclC6vPQZ00kPNq")

# Prepare the Actor input
run_input = {
    "searchStringsArray": ["Inspira Health Network"],
    "locationQuery": "New Jersey, USA",
    "maxCrawledPlacesPerSearch": 5,  # Get multiple locations
    "language": "en",
    "searchMatching": "all",
    "placeMinimumStars": "",  # Changed back to empty string as API expects string
    "website": "allPlaces",
    "skipClosedPlaces": False,
    "scrapePlaceDetailPage": True,  # Get detailed info including contact
    "scrapeTableReservationProvider": False,
    "includeWebResults": False,
    "scrapeDirectories": False,
    "maxQuestions": 0,
    "scrapeContacts": True,  # Enable contact scraping
    "maximumLeadsEnrichmentRecords": 0,
    "maxReviews": 0,
    "reviewsSort": "newest",
    "reviewsFilterString": "",
    "reviewsOrigin": "all",
    "scrapeReviewsPersonalData": True,
    "maxImages": 0,
    "scrapeImageAuthors": False,
    "allPlacesNoSearchAction": "",
}

# Run the Actor and wait for it to finish
run = client.actor("nwua9Gu5YrADL7ZDj").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)