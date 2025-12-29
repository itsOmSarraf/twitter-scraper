#!/usr/bin/env python3
"""
Twitter/X Scraper with JSON input and output.
Accepts a username and optional search query parameter.
"""

import json
import time
import re
import os
import random
import sys
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    """Setup and return a Chrome WebDriver instance with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--mute-audio")
    
    # Add user agent to appear more like a real browser
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    try:
        # First approach - Use webdriver manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"First driver initialization approach failed: {e}")
        print("Trying alternative approach...")
        
        try:
            # Second approach - Use Chrome directly without service
            driver = webdriver.Chrome(options=chrome_options)
            return driver
        except Exception as e2:
            print(f"All driver initialization approaches failed")
            print("Please make sure Chrome is installed correctly.")
            sys.exit(1)

def check_for_login_wall(driver):
    """Check if we've hit a login wall and need to log in."""
    try:
        login_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Log in')]")
        signup_elements = driver.find_elements(By.XPATH, "//span[contains(text(), 'Sign up')]")
        
        if login_elements or signup_elements:
            print("Detected a login wall. You may need to manually log in.")
            print("The script will wait 45 seconds for you to login...")
            time.sleep(45)  # Wait for manual login
            return True
    except Exception as e:
        print(f"Error checking for login wall: {e}")
    
    return False

def clean_tweet_text(text):
    """Clean the tweet text by removing extra spaces and newlines."""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def random_scroll(driver):
    """Perform a random scroll to appear more human-like."""
    scroll_height = random.randint(300, 1000)
    driver.execute_script(f"window.scrollBy(0, {scroll_height});")

def extract_tweet_data(article, username):
    """Extract data from a tweet article element."""
    try:
        # Extract timestamp
        time_element = article.find('time')
        timestamp = time_element['datetime'] if time_element else "Unknown"
        
        # Extract tweet URL/ID
        if time_element and time_element.parent and time_element.parent.parent:
            tweet_link = time_element.parent.parent.get('href')
            tweet_id = tweet_link.split('/')[-1] if tweet_link else "Unknown"
        else:
            tweet_id = "Unknown"
        
        # Extract tweet text
        tweet_text_div = article.find('div', {'data-testid': 'tweetText'})
        if tweet_text_div:
            tweet_text = clean_tweet_text(tweet_text_div.get_text())
        else:
            tweet_text = "No text found"
        
        # Extract likes, retweets, replies
        stats_divs = article.find_all('div', {'role': 'group'})
        stats = {}
        if stats_divs:
            stats_elements = stats_divs[0].find_all('div')
            for i, stat_type in enumerate(['replies', 'retweets', 'likes']):
                if i < len(stats_elements):
                    stat_text = stats_elements[i].get_text()
                    stat_value = re.search(r'\d+', stat_text)
                    stats[stat_type] = int(stat_value.group()) if stat_value else 0
        
        # Add tweet to our list
        tweet_data = {
            'tweet_id': tweet_id,
            'timestamp': timestamp,
            'text': tweet_text,
            'replies': stats.get('replies', 0),
            'retweets': stats.get('retweets', 0),
            'likes': stats.get('likes', 0),
            'url': f"https://twitter.com/{username}/status/{tweet_id}" if tweet_id != "Unknown" else "Unknown"
        }
        
        return tweet_data
    except Exception as e:
        print(f"Error extracting tweet data: {e}")
        return None

def scrape_tweets(driver, username, search_query=None, max_scrolls=200, scroll_pause_time=2.5, scroll_variation=1.0):
    """Scrape tweets by scrolling through the timeline."""
    tweets = []
    unique_tweet_ids = set()  # To check for duplicates based on ID
    unique_tweet_texts = set()  # Fallback for duplicate detection
    scroll_count = 0
    consecutive_no_new_tweets = 0
    
    # Determine the target URL based on presence of search query
    if search_query:
        # For direct search format (from:username search_query)
        encoded_query = f"from%3A{username}%20{search_query.replace(' ', '%20')}"
        target_url = f"https://x.com/search?q={encoded_query}&src=typed_query"
    else:
        # For all user's tweets and replies
        target_url = f"https://x.com/{username}/with_replies"
    
    print(f"Starting to scrape tweets from {target_url}")
    driver.get(target_url)
    
    # Check for login wall before proceeding
    if check_for_login_wall(driver):
        driver.get(target_url)  # Reload the target page after login
    
    # Wait for the timeline to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'article'))
        )
    except TimeoutException:
        print("Timeout while waiting for the timeline to load.")
        return tweets
    
    time.sleep(3)  # Allow some time for the page to fully load
    
    # Scroll and scrape
    while scroll_count < max_scrolls:
        # Every 10 scrolls, perform some random actions to appear more human-like
        if scroll_count % 10 == 0:
            random_scroll(driver)
            time.sleep(random.uniform(1.0, 3.0))
        
        # Parse the page with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all tweet articles
        articles = soup.find_all('article')
        
        new_tweets_found = 0
        
        for article in articles:
            tweet_data = extract_tweet_data(article, username)
            
            if not tweet_data:
                continue
                
            # Check if we've already seen this tweet
            if tweet_data['tweet_id'] != "Unknown" and tweet_data['tweet_id'] in unique_tweet_ids:
                continue
                
            # Fallback check for duplicates based on content
            if tweet_data['text'] in unique_tweet_texts:
                continue
                
            # Add the tweet to our results
            tweets.append(tweet_data)
            new_tweets_found += 1
            
            # Record the ID and text to avoid duplicates
            if tweet_data['tweet_id'] != "Unknown":
                unique_tweet_ids.add(tweet_data['tweet_id'])
            unique_tweet_texts.add(tweet_data['text'])
            
        # Scroll down to load more tweets
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time + random.uniform(-scroll_variation, scroll_variation))
        scroll_count += 1
        
        # If we didn't find any new tweets, increment the counter
        if new_tweets_found == 0:
            consecutive_no_new_tweets += 1
        else:
            consecutive_no_new_tweets = 0
            
        # If we've gone 5 scrolls without finding new tweets, stop
        if consecutive_no_new_tweets >= 5:
            print(f"No new tweets found in the last 5 scrolls. Stopping.")
            break
            
        # Print progress
        if scroll_count % 10 == 0:
            print(f"Scrolled {scroll_count} times, found {len(tweets)} tweets so far")
            
    print(f"Scraping complete. Found {len(tweets)} unique tweets.")
    return tweets

def save_tweets_to_json(tweets, filename):
    """Save tweet data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(tweets, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(tweets)} tweets to {filename}")

def process_json_input(json_input):
    """Process the JSON input data."""
    try:
        data = json.loads(json_input)
        username = data.get('username')
        search_query = data.get('search_query', None)
        max_scrolls = data.get('max_scrolls', 200)
        scroll_pause_time = data.get('scroll_pause_time', 2.5)
        
        if not username:
            raise ValueError("Username is required in the JSON input")
            
        return {
            'username': username,
            'search_query': search_query,
            'max_scrolls': max_scrolls,
            'scroll_pause_time': scroll_pause_time
        }
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Twitter/X Scraper with JSON input')
    parser.add_argument('--json', type=str, help='JSON string with configuration')
    parser.add_argument('--json-file', type=str, help='Path to JSON file with configuration')
    args = parser.parse_args()
    
    # Process JSON input
    if args.json:
        config = process_json_input(args.json)
    elif args.json_file:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            config = process_json_input(f.read())
    else:
        # Interactive mode
        print("Enter JSON configuration:")
        json_input = input()
        config = process_json_input(json_input)
    
    # Initialize the scraper
    username = config['username']
    search_query = config['search_query']
    max_scrolls = config['max_scrolls']
    scroll_pause_time = config['scroll_pause_time']
    scroll_variation = 1.0  # Random variation in scroll time
    
    output_file = f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    if search_query:
        output_file = f"{username}_{search_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Setup driver and scrape tweets
    driver = setup_driver()
    try:
        tweets = scrape_tweets(
            driver, 
            username, 
            search_query, 
            max_scrolls, 
            scroll_pause_time,
            scroll_variation
        )
        save_tweets_to_json(tweets, output_file)
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 