import requests

url = "https://jsearch.p.rapidapi.com/search"

querystring = {"query":"developer jobs in chicago","page":"1","num_pages":"1","country":"us","date_posted":"all"}

headers = {
	"x-rapidapi-key": "0597028da3mshba0adfb0a4deeafp136104jsn630c8f1a47e0",
	"x-rapidapi-host": "jsearch.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())