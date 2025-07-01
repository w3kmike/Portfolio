import pandas as pd, requests, flask
from IPython.display import display
import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


def download_file(url, folder):
    local_filename = os.path.join(folder, os.path.basename(urlparse(url).path))
    if not os.path.exists(local_filename):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                f.write(r.content)
            print(f"Downloaded: {url}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")
    return local_filename

def clone_website(base_url, output_folder="cloned_site"):
    os.makedirs(output_folder, exist_ok=True)

    # Fetch HTML content
    response = requests.get(base_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Save the main HTML
    index_path = os.path.join(output_folder, "index.html")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

    # Download assets: images, CSS, JS
    tags_attrs = {
        "img": "src",
        "link": "href",
        "script": "src"
    }

    for tag, attr in tags_attrs.items():
        for resource in soup.find_all(tag):
            file_url = resource.get(attr)
            if file_url:
                full_url = urljoin(base_url, file_url)
                local_file = download_file(full_url, output_folder)
                # Replace original link in soup for future use if needed
                if os.path.exists(local_file):
                    resource[attr] = os.path.basename(local_file)

    # Save modified HTML with local paths
    with open(os.path.join(output_folder, "index_local.html"), 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    print(f"Website cloned to ./{output_folder}/")

# Example usage
if __name__ == "__main__":
    url = input("Enter the URL of the website to clone: ")
    clone_website(url)
