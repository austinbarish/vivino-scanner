import PyPDF2
import time
import json
from tqdm import tqdm
from typing import List, Dict
import pandas as pd
from dotenv import load_dotenv
import os


def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        dict: Dictionary containing page numbers and their corresponding text
    """
    # Dictionary to store text from each page
    text_by_page = {}

    try:
        # Open the PDF file in binary read mode
        with open(pdf_path, "rb") as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)

            # Get the number of pages
            num_pages = len(pdf_reader.pages)

            # Extract text from each page
            for page_num in range(num_pages):
                # Get the page object
                page = pdf_reader.pages[page_num]

                # Extract text from the page
                text = page.extract_text()

                # Store the text in our dictionary
                text_by_page[page_num + 1] = text

        return text_by_page

    # Error Messaging
    except FileNotFoundError:
        print(f"Error: The file {pdf_path} was not found.")
        return None
    except PyPDF2.PdfReadError:
        print("Error: Invalid or corrupted PDF file.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None


import google.generativeai as genai
from typing import List, Dict
import json
import PyPDF2

# Made with Claude 3.5


class GeminiWineParser:
    def __init__(self, api_key: str):
        """Initialize the Gemini parser with API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def parse_wine_list(self, text: str) -> List[Dict]:
        """
        Parse wine list text using Gemini 1.5

        Args:
            text (str): The wine list text to parse

        Returns:
            List[Dict]: List of parsed wine entries
        """
        prompt = f"""Extract wine information from the text below into a structured format.
        For each wine entry, extract:
        - ID number
        - Producer
        - Wine name
        - Type (e.g., NON-VINTAGE, BLANC DE BLANCS)
        - Main Type (e.g., SPARKLING, WHITE, RED, ROSE)
        - Region
        - Vintage (if available)
        - Price
        - Size (glass, bottle, half bottle, magnum)
        
        Format as JSON with missing fields as null but get as many wines as possible even if some fields are missing.
        
        Text to parse:
        {text}
        
        Respond with only valid JSON in this exact format:
        {{
            "wines": [
                {{
                    "id": "1234",
                    "producer": "Producer Name",
                    "name": "Wine Name",
                    "type": "Wine Type",
                    "region": "Region",
                    "country": "Country",
                    "vintage": "2020",
                    "price": "123",
                    "size": "bottle"
                }}
            ]
        }}"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.0,  # Use deterministic output
                    "top_p": 1.0,
                    "top_k": 1,
                },
            )

            # Find the JSON in the response
            response_text = response.text
            # Look for JSON between ```json and ``` if present
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            # Parse the JSON response
            json_response = json.loads(json_str)
            return json_response["wines"]

        except Exception as e:
            print(f"Error parsing wine list: {str(e)}")
            return []

    def parse_pdf_and_wine_list(
        self, pdf_path: str, page_number: int = 1
    ) -> List[Dict]:
        """
        Extract text from PDF and parse wine list

        Args:
            pdf_path (str): Path to PDF file
            page_number (int): Page number to parse (default: 1)

        Returns:
            List[Dict]: List of parsed wine entries
        """
        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                if page_number <= len(reader.pages):
                    text = reader.pages[page_number - 1].extract_text()
                    return self.parse_wine_list(text)
                else:
                    raise ValueError(f"PDF has only {len(reader.pages)} pages")
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return []

    def save_to_json(self, wines: List[Dict], output_file: str):
        """Save parsed wines to a JSON file"""
        try:
            with open(output_file, "w") as f:
                json.dump({"wines": wines}, f, indent=2)
            print(f"Successfully saved to {output_file}")
        except Exception as e:
            print(f"Error saving to file: {str(e)}")


import requests
from bs4 import BeautifulSoup
import re


def create_csv_menu(pdf_path, csv_path, page_nums=0, editor=False):
    """
    Parse PDF menu to CSV with manual correction capability

    Args:
        pdf_path (str): Path to PDF file
        page_nums (int): Page number to parse (default: 0 for all pages)

    Returns:
        str: Path to saved CSV file
    """
    print("INITIALIZING")
    # Initialize parser
    load_dotenv(dotenv_path="config.env")
    google_key = os.getenv("GOOGLE_KEY")
    parser = GeminiWineParser(google_key)

    # Parse PDF
    print("EXTRACTING TEXT")
    pages = extract_text_from_pdf(pdf_path)
    print(pages[1])
    print("DONE EXTRACTING TEXT")

    max_pages = max(pages.keys())
    pages_to_process = page_nums if page_nums > 0 else max_pages

    # Process each page individually
    all_results = []
    for page_num in range(1, pages_to_process + 1):
        print(f"\nProcessing page {page_num}/{pages_to_process}")
        page_text = pages[page_num]
        print(f"Page {page_num} text length: {len(page_text)} characters")

        # Skip empty pages
        if not page_text.strip():
            print(f"Skipping page {page_num} - empty text")
            continue

        # Parse the page
        try:
            page_results = parser.parse_wine_list(page_text)
            print(f"Found {len(page_results)} wines on page {page_num}")
            all_results.extend(page_results)
        except Exception as e:
            print(f"Error parsing page {page_num}: {str(e)}")
            continue

        # Add page number to all_results

    print("PARSING WINE LIST")
    print("DONE PARSING WINE LIST")
    # Convert to DataFrame
    df = pd.DataFrame(all_results)
    print("TOTAL WINES: ", len(df))
    if editor:
        # Display DataFrame for review
        print("\nPlease review the parsed data:")
        print(df)

        while True:
            edit = input("\nWould you like to make any corrections? (yes/no): ").lower()
            if edit == "no":
                break
            elif edit == "yes":
                try:
                    print("\nCurrent columns:", df.columns.tolist())
                    col = input("Enter column name to edit: ")
                    row = int(input("Enter row number to edit (0-based index): "))
                    new_value = input("Enter new value: ")
                    df.at[row, col] = new_value
                    print("\nUpdated DataFrame:")
                    print(df)
                except Exception as e:
                    print(f"Error making edit: {str(e)}")
            else:
                print("Please enter 'yes' or 'no'")

    # Save to CSV
    df.to_csv(csv_path, index=False)
    print(f"\nSaved corrected data to: {csv_path}")
    return df


def vivino_search(name, producer, type, region, country, vintage, menu_price):

    # Define the base URL
    base_url = "https://www.vivino.com/search/wines"

    # Create the search query
    query = f"{name} {producer} {type} {vintage} {region} {country}"

    # Send request to Vivino search page
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0"
    }

    # Send GET request
    response = requests.get(base_url, params=params, headers=headers)

    # Check if request was successful
    if response.status_code != 200:
        print("Failed to fetch data")
        return None

    # Parse the HTML response
    soup = BeautifulSoup(response.text, "html.parser")

    # Find first wine result
    first_result = soup.select_one(".card.card-lg")
    if not first_result:
        print("No results found.")
        return None

    # Extract wine details
    try:
        wine_name = first_result.select_one(".wine-card__name").text.strip()
        link = "https://www.vivino.com" + first_result.select_one("a")["href"]
        country = first_result.select_one(
            ".wine-card__region [data-item-type='country']"
        ).text.strip()
        region = first_result.select_one(
            ".wine-card__region .link-color-alt-grey"
        ).text.strip()
        rating = (
            first_result.select_one(".average__number").text.strip()
            if first_result.select_one(".average__number")
            else "N/A"
        )
        num_ratings = (
            first_result.select_one(".text-micro").text.split(" ratings")[0].strip()
            if first_result.select_one(".text-micro")
            else "N/A"
        )
        price = (
            first_result.select_one(".wine-price-value").text.strip()
            if first_result.select_one(".wine-price-value")
            else "N/A"
        )

    except AttributeError:
        print("Error extracting data")
        return None

    # print("Result found:", wine_name)

    # print("Checking link:", link)

    link_response = requests.get(link, headers=headers)
    if link_response.status_code != 200:
        print("Failed to fetch data")
        return None
    link_soup = BeautifulSoup(link_response.text, "html.parser")

    # Save the data as link.txt
    with open("link.txt", "w") as f:
        f.write(str(link_soup))

    try:
        food_container = link_soup.select_one(".foodPairing__foodContainer--1bvxM")

        # Extract food pairing names
        food_pairings = [
            str(a).split('aria-label="')[1].split('"')[0]
            for a in food_container.find_all("a")
        ]

    except AttributeError:
        # print("Error extracting food pairings")
        food_pairings = []

    # Extract price if not available
    if len(price) <= 1:
        # print("Price not available. Extracting from page")
        try:
            script_tag = link_soup.find("script", {"type": "application/ld+json"})

            # Load the JSON data
            json_data = json.loads(script_tag.string)

            # Extract the price
            price = json_data.get("offers", {}).get("price")

            if price is None:
                # Find the price element
                price_element = link_soup.find(
                    "span", class_="purchaseAvailabilityPPC__amount--2_4GT"
                )

                # Extract the text and clean it
                price = price_element.text.strip() if price_element else "N/A"

        except AttributeError:
            print("Error extracting price")

    # Check if price is a number
    if price != "N/A" and price != "-":
        price = price.replace("$", "")
        price = price.replace(" ", "")
        price = price.replace("€", "")
        price = price.replace("£", "")
        price = price.replace("¥", "")
        price = price.replace("₩", "")
        price = price.replace("₹", "")

        try:
            price = float(price)
            price_multiplier = menu_price / price
        except ValueError:
            print("Error converting price to float")
            price_multiplier = "N/A"
    else:
        price_multiplier = "N/A"

    # Create output
    # Return wine data
    data = {
        "name": wine_name,
        "link": link,
        "country": country,
        "region": region,
        "rating": rating,
        "num_ratings": num_ratings,
        "price": price,
        "price_multiplier": price_multiplier,
        "food_pairings": food_pairings,
    }

    return data


from tqdm import tqdm
import time
import multiprocessing


# Get wine data for all wines in the dataframe
def vivino_search_all(df):
    print("STARTING VIVINO SEARCH")
    # Create a copy of the dataframe
    new_df = df.copy()

    # Create lists to store the results
    food_pairings = []
    prices = []
    price_multipliers = []
    ratings = []
    num_ratings = []
    links = []

    # Set fail count to quite if 5 fails in a row
    fail_count = 0

    # Iterate over each row in the dataframe
    for index, row in tqdm(new_df.iterrows(), total=len(new_df)):
        # Get wine data
        wine_data = vivino_search(
            name=row["name"] if "name" in row and pd.notna(row["name"]) else " ",
            producer=(
                row["producer"]
                if "producer" in row and pd.notna(row["producer"])
                else " "
            ),
            type=row["type"] if "type" in row and pd.notna(row["type"]) else " ",
            region=(
                row["region"] if "region" in row and pd.notna(row["region"]) else " "
            ),
            country=(
                row["country"] if "country" in row and pd.notna(row["country"]) else " "
            ),
            vintage=(
                row["vintage"] if "vintage" in row and pd.notna(row["vintage"]) else " "
            ),
            menu_price=(
                row["price"] if "price" in row and pd.notna(row["price"]) else " "
            ),
        )

        # Append the data to the list
        if wine_data:
            food_pairings.append(wine_data["food_pairings"])
            prices.append(wine_data["price"])
            ratings.append(wine_data["rating"])
            links.append(wine_data["link"])
            price_multipliers.append(wine_data["price_multiplier"])
            num_ratings.append(wine_data["num_ratings"])
            fail_count = 0

        else:
            food_pairings.append("N/A")
            prices.append("N/A")
            ratings.append("N/A")
            links.append("N/A")
            price_multipliers.append("N/A")
            num_ratings.append("N/A")
            fail_count += 1

        if fail_count >= 5:
            print("Failed 5 times in a row. Pausing for 3 minutes.")
            time.sleep(180)

        # Pause for a half second to avoid rate limiting
        time.sleep(0.51)

    # Add the lists to the dataframe
    new_df["food_pairings"] = food_pairings
    new_df["vivino_price"] = prices
    new_df["price_multiplier"] = price_multipliers
    new_df["rating"] = ratings
    new_df["link"] = links
    new_df["num_ratings"] = num_ratings

    # Rename the price column to menu_price
    new_df.rename(columns={"price": "menu_price"}, inplace=True)

    return new_df
