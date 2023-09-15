import os
import requests
from bs4 import BeautifulSoup
import argparse

def get_raw_text_from_links(file_path):
    try:
        with open(file_path, 'r') as link_file:
            links = link_file.read().splitlines()

        for link in links:
            # Send an HTTP GET request to the URL
            response = requests.get(link)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the HTML content of the page
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract and clean all visible text
                visible_text = ' '.join(soup.stripped_strings)

                # Create a log file with a unique name based on the link
                file_name = f"scraped_data_{os.path.basename(link)}.txt"

                # Write the visible text to the log file
                with open(file_name, 'w', encoding='utf-8') as log_file:
                    log_file.write(visible_text)

                print(f"Scraped data from {link} and saved to {file_name}")

            else:
                print(f"Failed to retrieve content from {link}. Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {e}")

def main(file_path):
    get_raw_text_from_links(file_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Website Scraper")
    parser.add_argument("file_path", help="Path to a text file containing a list of links")
    args = parser.parse_args()

    main(args.file_path)
