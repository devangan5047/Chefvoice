import requests

url = "https://www.indianhealthyrecipes.com/butter-chicken/"

res = requests.post("http://127.0.0.1:5000/scrape", json={"url": url})
print(res.status_code)
print(res.json())
