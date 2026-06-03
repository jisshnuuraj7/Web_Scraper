import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import sys
import os

# Ensure stdout uses UTF-8 to support emojis on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def scrape_imdb_top_250():
    print(" Starting IMDb Top 250 Movies Scraper...")
    print(" Setting up headless Chrome WebDriver...")

    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    movies_data = []

    try:
        url = "https://www.imdb.com/chart/top/"
        print(f" Opening IMDb Top 250 page: {url}")
        driver.get(url)

        print(" Waiting for page elements to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item"))
        )
        time.sleep(1)

        print(" Searching for movie list elements...")
        movie_elements = driver.find_elements(By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")
        total_found = len(movie_elements)
        print(f" Found {total_found} movie elements. Extracting...")

        for index, movie in enumerate(movie_elements):
            if index >= 250:
                break

            try:
                lines = [line.strip() for line in movie.text.split('\n') if line.strip()]

                if not lines:
                    continue

                # Parse Rank
                rank = "N/A"
                for line in lines:
                    if line.startswith("#") and line[1:].isdigit():
                        rank = int(line.replace("#", ""))
                        break
                if rank == "N/A":
                    rank = index + 1

                # Parse Title
                title = "N/A"
                for i, line in enumerate(lines):
                    if line == f"#{rank}":
                        if i + 1 < len(lines):
                            title = lines[i + 1]
                            break
                if title == "N/A" and lines:
                    title = lines[0]

                # Parse Year
                year = "N/A"
                for line in lines:
                    if len(line) >= 4 and line[:4].isdigit():
                        year = int(line[:4])
                        break

                # Parse Rating
                rating = "N/A"
                for line in lines:
                    parts = line.split()
                    if parts:
                        val = parts[0]
                        try:
                            float_val = float(val)
                            if 1.0 <= float_val <= 10.0:
                                rating = float_val
                                break
                        except ValueError:
                            continue

                movies_data.append({
                    "Rank": rank,
                    "Title": title,
                    "Year": year,
                    "Rating": rating
                })

                print(f" Scraped #{rank}: {title} ({year}) | Rating: {rating}")

            except Exception as e:
                continue

    except Exception as e:
        print(f" An error occurred: {e}")

    finally:
        print(" Closing the browser...")
        driver.quit()
        print(" Browser closed.")

    if not movies_data:
        print(" No data was scraped!")
        return

    print(f"\n Total scraped: {len(movies_data)} / 250")

    df = pd.DataFrame(movies_data)

    # ── Save to CSV
    csv_filename = "imdb_top250.csv"
    df.to_csv(csv_filename, index=False)
    print(f" CSV saved → {csv_filename}")

    # ── Save to Excel 
    excel_filename = "imdb_top250.xlsx"
    df.to_excel(excel_filename, index=False, sheet_name="IMDb Top 250")
    print(f" Excel saved → {excel_filename}")

    # ── Preview top 10 in terminal 
    print("\n --- Preview of Top 10 Results ---")
    print(df.head(10).to_string(index=False))
    print("------------------------------------\n")

    # ── Auto open Excel file 
    print(f"Opening '{excel_filename}'...")
    try:
        os.startfile(excel_filename)
        print("Excel file opened!")
    except Exception as e:
        print(f"Could not open automatically: {e}")

if __name__ == "__main__":
    scrape_imdb_top_250()