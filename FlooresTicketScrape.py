#!/usr/bin/env python
# coding: utf-8

# Floores Scraper (GitHub-Compatible Headless Mode)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Setup Chrome with GitHub Actions–friendly headless options
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")

# Launch browser
driver = webdriver.Chrome(options=options)

# Load the events page
driver.get("https://www.liveatfloores.com/allevents/")

# Wait until the event titles are loaded
WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "a#eventTitle"))
)

# Grab all event entries
event_links = driver.find_elements(By.CSS_SELECTOR, "a#eventTitle")

print(f"Found {len(event_links)} event blocks.")

events = []

for event_link in event_links:
    try:
        # Title and detail URL
        h2 = event_link.find_element(By.TAG_NAME, "h2")
        title_text = h2.text.strip()
        detail_url = event_link.get_attribute("href")

        # Navigate up to the wrapper
        wrapper = event_link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rhp-event')]")

        # Event day
        try:
            date_div = wrapper.find_element(By.ID, "eventDate")
            event_day = date_div.text.strip()
        except:
            event_day = ""

        # Event time
        try:
            time_spans = wrapper.find_elements(By.CSS_SELECTOR, "span.rhp-event__time-text--list")
            actual_times = [span.text.strip() for span in time_spans if "door" not in span.text.lower()]
            event_time = actual_times[0] if actual_times else ""
        except:
            event_time = ""

        # Ticket link and status
        try:
            etix_btn = wrapper.find_element(By.CSS_SELECTOR, ".rhp-event-cta.on-sale a.btn")
            etix_url = etix_btn.get_attribute("href")
            ticket_status = "Etix Available"
        except:
            etix_url = ""
            if "free" in title_text.lower():
                ticket_status = "Free Show"
            else:
                ticket_status = "Sold Out"

        print(f"→ {title_text} | {ticket_status} | {event_day} | {event_time}")

        events.append({
            "title": title_text,
            "event_detail_url": detail_url,
            "etix_url": etix_url,
            "ticket_status": ticket_status,
            "event_day": event_day,
            "event_time": event_time
        })

    except Exception as e:
        print("Error parsing event:", e)

driver.quit()

# Save to DataFrame and CSV
df = pd.DataFrame(events)
df.to_csv("floores_all_events_full.csv", index=False)
print("\n✅ Saved to 'floores_all_events_full.csv'")
print(df)
