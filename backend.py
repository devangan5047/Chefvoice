from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# 🔑 Replace with your actual keys
API_KEY = "AIzaSyCEKDo2egDI3EWjgHDDcMtR4qKk-dTMPWI"
CX_ID = "6770fc55e14744bab"

# ✅ Step 1: Google Search via CSE
def search_recipe(dish_name):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX_ID,
        "q": f"{dish_name} recipe"
    }

    res = requests.get(url, params=params)
    if res.status_code != 200:
        return None

    data = res.json()
    items = data.get("items", [])
    if not items:
        return None

    top_result = items[0]
    return {
        "title": top_result["title"],
        "link": top_result["link"],
        "snippet": top_result.get("snippet", "")
    }

@app.route("/get-recipe", methods=["POST"])
def get_recipe():
    data = request.get_json()
    dish = data.get("dish")

    if not dish:
        return jsonify({"error": "Dish not specified"}), 400

    result = search_recipe(dish)

    if result:
        return jsonify({"response": result})
    else:
        return jsonify({"error": "No recipe found"}), 404

# ✅ Step 2: Scrape the recipe page
def scrape_recipe(url):
    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.content, "lxml")

        # Ingredients extraction (loose matching)
        ingredients = []
        for tag in soup.find_all(["li", "span"]):
            classes = " ".join(tag.get("class", []))
            if any(word in classes.lower() for word in ["ingredient", "ingredients-item-name"]):
                text = tag.get_text(strip=True)
                if text and text not in ingredients:
                    ingredients.append(text)

        # Instructions extraction (loose matching)
        instructions = []
        for tag in soup.find_all(["li", "p"]):
            classes = " ".join(tag.get("class", []))
            if any(word in classes.lower() for word in ["instruction", "instructions-section-item"]):
                step = tag.get_text(strip=True)
                if step and step not in instructions:
                    instructions.append(step)

        # Fallback: use <p> with long enough text
        if not instructions:
            instructions = [
                p.get_text(strip=True) for p in soup.find_all("p")
                if len(p.get_text(strip=True).split()) > 5
            ][:15]

        return {
            "ingredients": ingredients[:15],
            "instructions": instructions[:15]
        }

    except Exception as e:
        print("❌ Scraping error:", e)
        return None

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    result = scrape_recipe(url)
    if not result:
        return jsonify({"error": "Failed to scrape recipe"}), 500

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
