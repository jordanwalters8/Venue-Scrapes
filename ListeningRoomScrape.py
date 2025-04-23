#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# Listening Room

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

# Setup Selenium
options = webdriver.ChromeOptions()
# options.add_argument('--headless')  # Uncomment to hide the browser
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

# Navigate to shows page
driver.get("https://www.listeningroomcafe.com/nashville-shows")
time.sleep(3)

# List to store event data
events = []

# Loop through pages 1, 2, 3
for page_number in range(1, 4):
    print(f"\n🔄 Scraping Page {page_number}...")
    
    if page_number > 1:
        try:
            page_link = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, f'a.pager__number[data-page-number="{page_number}"]')))
            page_link.click()
            time.sleep(2)
        except Exception as e:
            print(f"❌ Couldn't click to page {page_number}: {e}")
            continue

    # Get all clickable show tiles
    show_tiles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "grid-product__image")))

    for tile_index in range(len(show_tiles)):
        # Re-fetch the clickable tiles each time to avoid stale elements
        show_tiles = driver.find_elements(By.CLASS_NAME, "grid-product__image")
        if tile_index >= len(show_tiles):
            continue

        try:
            show_tiles[tile_index].click()
            time.sleep(1.5)

            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-details__product-sku")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            artist = soup.find('h1', class_='product-details__product-title')
            artist = artist.text.strip() if artist else 'N/A'

            room = soup.find('div', class_='label__text')
            room = room.text.strip() if room else 'N/A'
            capacity = 255 if "MAIN STAGE" in room.upper() else 75 if "FRONT CAFE" in room.upper() else None

            datetime = soup.find('div', class_='product-details__product-sku')
            datetime = datetime.text.strip() if datetime else 'N/A'

            price = soup.find('span', class_='details-product-price__value')
            price = price.text.strip() if price else 'N/A'

            tickets_tag = soup.find('div', class_='product-details-module__title')
            if tickets_tag:
                match = re.search(r'(\d+)\s+available', tickets_tag.get_text())
                tickets_left = int(match.group(1)) if match else None
            else:
                tickets_left = None

            percent_sold = round(100 * (1 - tickets_left / capacity), 1) if capacity and tickets_left is not None else None

            events.append({
                'Artist/Event': artist,
                'Date/Time': datetime,
                'Room': room,
                'Capacity': capacity,
                'Tickets Left': tickets_left,
                '% Sold': percent_sold,
                'Price': price
            })

            driver.back()
            time.sleep(1.5)
        except Exception as e:
            print(f"⚠️ Error scraping show {tile_index+1} on page {page_number}: {e}")
            driver.back()
            time.sleep(1.5)
            continue

driver.quit()

# Build DataFrame
df = pd.DataFrame(events)

# Save to CSV
df.to_csv("listening_room_shows.csv", index=False)
print("\n✅ Data saved to 'listening_room_shows.csv'")

# Enhance with date/time & price analysis
df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
df['Day of Week'] = df['Date/Time'].dt.day_name()
df['Hour'] = df['Date/Time'].dt.hour
df['Price ($)'] = df['Price'].replace(r'[\$,]', '', regex=True).astype(float)

# Compare price to average for same day+hour
avg_price = df.groupby(['Day of Week', 'Hour'])['Price ($)'].transform('mean')
df['Above Avg for Day+Hour'] = df['Price ($)'] > avg_price

# Show final results
print("\n🎤 Final Scraped Shows with Pricing Analysis:\n")
print(df[['Artist/Event', 'Date/Time', 'Room', 'Price ($)', 'Tickets Left', '% Sold', 'Above Avg for Day+Hour']].to_string(index=False))

# Save FINAL DataFrame to CSV
df.to_csv("listening_room_shows.csv", index=False)
print("✅ Final CSV saved with pricing analysis included.")

