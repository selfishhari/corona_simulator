"""
This script scrapes the latest data from https://www.health.gov.au/news/health-alerts/novel-coronavirus-2019-ncov-health-alert/coronavirus-covid-19-current-situation-and-case-numbers
"""

import requests, datetime
from selenium import webdriver
import pandas as pd

URL = "https://www.health.gov.au/news/health-alerts/novel-coronavirus-2019-ncov-health-alert/coronavirus-covid-19-current-situation-and-case-numbers"



def get_todays_data():
    
    print("Scraping....")
    
    driver = webdriver.Chrome()

    driver.get(URL)
    
    print("got url")
    
    table = driver.find_element_by_tag_name("table")#.screenshot("abc.png")
    
    print("got table")
    
    aus_data_today = pd.read_html(driver.page_source)[0]
    
    print("scraping complete")

    return aus_data_today

def clean_scraped_data(df):
    
    df["Location"].replace("Total**", "Australia", inplace=True)

    df = df.iloc[:-1, :]

    df["Date"] = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")

    df["Date"] = pd.to_datetime(df["Date"])

    df.columns = ["Province/State", "Confirmed", "Date"]
    
    df["Province/State"] = df["Province/State"].str.strip()
    
    df["Confirmed"] = df["Confirmed"].astype("float")
    
    print("cleaning complete", df)

    #df.set_index("Province/State", inplace=True)

    return df

def merge_to_historical(hist, today):
    
    hist = hist.copy()
    
    if not (hist.Date.max() == today.Date.min()):
    
        merged_data = pd.concat([hist, today], axis=0)
        
    else:
        
        merged_data = hist
            
    return merged_data

def merge_latest(latest, today):
    
    """
    Since latest death and recovered are not updated in the website, I will be using yesterday's death/recovered
    """
    latest = latest.copy()
    
    del latest["Confirmed"]
    del latest["Date"]
    
    today = today.merge(latest, how="left", on="Province/State")
    
    return today

def scrape_and_update(hist):
    
    latest = hist.loc[hist["Date"] == hist["Date"].max(), :].copy()
    
    today = clean_scraped_data(get_todays_data())
    
    today_updated = merge_latest(latest, today)
    
    merged_data = merge_to_historical(hist, today_updated)
    
    print("Scraping complete")
    
    return merged_data
    