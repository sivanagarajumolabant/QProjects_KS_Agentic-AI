import time
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import os
import sys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

### Helper: Generate output filename from URL ###
def get_filename_from_url(url):
    parsed = urlparse(url)
    host = parsed.netloc  # e.g. "clutch.co"
    safe_name = host.replace('.', '_')  # e.g. "clutch_co"
    return f"{safe_name}_combined_pages.txt"

def setup_driver(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    # Mimic a common browser user-agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    # Enable verbose logging (optional)
    options.add_argument("--enable-logging=stderr")
    options.add_argument("--v=1")
    # Set an implicit wait for elements to be available
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver

def get_candidate_anchors(driver, keywords):
    """
    Return a list of all <a> elements whose visible text contains any keyword.
    Comparison is case-insensitive.
    """
    anchors = driver.find_elements(By.TAG_NAME, "a")
    candidates = []
    for a in anchors:
        text = a.text.strip().lower()
        if any(kw.lower() in text for kw in keywords):
            candidates.append(a)
    return candidates

def get_anchor_classes(anchor):
    """Return a set of CSS classes for a given anchor element."""
    classes_str = anchor.get_attribute("class")
    if classes_str:
        return set(classes_str.split())
    return set()

def compute_common_classes(candidates, min_occurrence=2):
    """
    Count CSS classes among candidate anchors and return those
    that appear in at least min_occurrence candidates.
    """
    class_freq = {}
    for a in candidates:
        classes = get_anchor_classes(a)
        for cls in classes:
            class_freq[cls] = class_freq.get(cls, 0) + 1
    return [cls for cls, count in class_freq.items() if count >= min_occurrence]

def find_nav_container_by_common_class(driver, candidates, common_class):
    """
    For candidate anchors having the common_class, traverse upward in the DOM
    until a container is found that holds at least two descendant anchors with that class.
    """
    for a in candidates:
        if common_class in get_anchor_classes(a):
            temp = a
            while temp:
                try:
                    parent = temp.find_element(By.XPATH, "./..")
                except Exception:
                    break
                try:
                    descendants = parent.find_elements(By.CSS_SELECTOR, f"a.{common_class}")
                except Exception:
                    descendants = []
                if len(descendants) >= 2:
                    return parent
                if parent.tag_name.lower() == "body":
                    break
                temp = parent
    return None

def extract_links_from_container(container, base_url):
    """Extract and normalize all nested anchor links from a given container."""
    nav_links = set()
    if container:
        anchors = container.find_elements(By.TAG_NAME, "a")
        for a in anchors:
            href = a.get_attribute("href")
            if href:
                nav_links.add(urljoin(base_url, href))
    return list(nav_links)

def get_nav_links_improved(driver, base_url, keywords):
    """
    Improved strategy:
      1. Find candidate <a> elements by keyword.
      2. Compute common CSS classes.
      3. Use a common class to locate the navigation container.
      4. Extract all nested links from that container.
    """
    candidates = get_candidate_anchors(driver, keywords)
    if not candidates:
        return []
    common_classes = compute_common_classes(candidates, min_occurrence=2)
    container = None
    if common_classes:
        # Choose the common class with the highest frequency among candidates.
        common_class = max(common_classes, key=lambda cls: sum(1 for a in candidates if cls in get_anchor_classes(a)))
        container = find_nav_container_by_common_class(driver, candidates, common_class)
        if container:
            print(f"Navigation container detected using common class: {common_class}")
    return extract_links_from_container(container, base_url) if container else []

def get_nav_links_by_fallback(driver, base_url):
    """
    Fallback strategy: Try to locate a <nav> element first; if not found, try <header>.
    """
    nav_links = set()
    try:
        navs = driver.find_elements(By.TAG_NAME, "nav")
        for nav in navs:
            for a in nav.find_elements(By.TAG_NAME, "a"):
                href = a.get_attribute("href")
                if href:
                    nav_links.add(urljoin(base_url, href))
    except Exception:
        pass
    if not nav_links:
        try:
            header = driver.find_element(By.TAG_NAME, "header")
            for a in header.find_elements(By.TAG_NAME, "a"):
                href = a.get_attribute("href")
                if href:
                    nav_links.add(urljoin(base_url, href))
        except Exception:
            pass
    return list(nav_links)

def get_navigation_links(driver, base_url):
    """
    Fully automated strategy:
      1. First, try to get links from a semantic <nav> tag.
      2. If that yields no links, try the improved common-class strategy.
      3. If still no links, fall back to searching for a <header>.
    """
    # Check for <nav> elements first.
    nav_links = set()
    try:
        navs = driver.find_elements(By.TAG_NAME, "nav")
        if navs:
            for nav in navs:
                for a in nav.find_elements(By.TAG_NAME, "a"):
                    href = a.get_attribute("href")
                    if href:
                        nav_links.add(urljoin(base_url, href))
            if nav_links:
                print("Navigation links detected using <nav> tag.")
                return list(nav_links)
    except Exception:
        pass

    # Use improved strategy.
    keywords = [
        "Home", "About", "Contact", "Service", "Services", "Client", "Clients",
        "Products", "Solutions", "Careers", "Team", "Company", "Portfolio",
        "Blog", "News", "Events", "Support", "FAQ", "Login", "Signup", "Register",
        "Store", "Shop", "Pricing", "Resources", "Industries", "Partners", "Investors",
        "Nutrition Insights", "WISEalliance"
    ]
    links = get_nav_links_improved(driver, base_url, keywords)
    if links:
        print("Navigation links detected using improved strategy.")
        return links

    print("Falling back to <header> search.")
    return get_nav_links_by_fallback(driver, base_url)

### Page Content Extraction Using Selenium ###
def fetch_page_content_selenium(driver, url):
    """
    Use Selenium to load a page and extract its header and text.
    Prefers <h1> as header; if not available, uses <title>.
    """
    try:
        driver.get(url)
        # Wait explicitly for the body element to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        html = driver.page_source
    except Exception as e:
        print(f"Error loading {url} with Selenium: {e}")
        return None, None

    soup = BeautifulSoup(html, 'html.parser')
    header_tag = soup.find('h1')
    if header_tag:
        header_text = header_tag.get_text(strip=True)
    else:
        title_tag = soup.find('title')
        header_text = title_tag.get_text(strip=True) if title_tag else "No Header Found"
    for tag in soup(["script", "style"]):
        tag.decompose()
    page_text = soup.get_text(separator="\n", strip=True)
    return header_text, page_text

# -------------------------------------------
# New: Process and Scrape Function for Tool Call
# -------------------------------------------
def scrape_and_process(url: str) -> str:
    """
    Given a URL (landing page), this function uses Selenium to:
      1. Load the landing page and extract navigation links.
      2. For each navigation link, load the page and extract header and text content.
      3. Combine the extracted texts, separating pages with a custom delimiter.
      
    Returns:
        str: Combined raw text from all navigation links.
    """
    # Use headless mode for production (set headless=True for HF Spaces)
    driver_nav = setup_driver(headless=True)
    driver_nav.get(url)
    # Wait until the body is loaded
    try:
        WebDriverWait(driver_nav, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        print(f"Timeout waiting for landing page to load: {e}")
    # Extract navigation links from the landing page
    nav_links = get_navigation_links(driver_nav, url)
    print(f"Found {len(nav_links)} navigation links: {nav_links}")
    driver_nav.quit()
    
    if not nav_links:
        raise Exception("No navigation links found using current methods.")
    
    combined_text = ""
    driver_content = setup_driver(headless=True)
    for link in nav_links:
        print(f"Processing: {link}")
        header_text, page_text = fetch_page_content_selenium(driver_content, link)
        if header_text and page_text:
            # Combine header and page text with the custom delimiter.
            combined_text += f"{header_text}\n\n{page_text}\n---PAGE DELIMITER---\n\n"
        else:
            combined_text += f"Error fetching content from {link}\n\n"
        time.sleep(1)  # Brief pause between pages
    driver_content.quit()
    
    return combined_text

# -------------------------------------------
# Main Function (for standalone testing)
# -------------------------------------------
### Main Workflow ###
def main():
    # Supply only the landing page URL.
    base_url = "https://www.krishnaik.in/"  # Replace with your landing page URL
    driver_nav = setup_driver(headless=True)
    driver_nav.get(base_url)
    try:
        WebDriverWait(driver_nav, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    except Exception as e:
        print(f"Timeout waiting for landing page to load: {e}")
    nav_links = get_navigation_links(driver_nav, base_url)
    print(f"Navigation links detected: {len(nav_links)}")
    for link in nav_links:
        print("  ", link)
    driver_nav.quit()
    
    if not nav_links:
        print("No navigation links found using current methods.")
        return

    output_filename = get_filename_from_url(base_url)
    driver_content = setup_driver(headless=True)
    with open(output_filename, "w", encoding="utf-8") as f:
        for link in nav_links:
            print(f"Processing: {link}")
            header_text, page_text = fetch_page_content_selenium(driver_content, link)
            if header_text and page_text:
                f.write(header_text + "\n")
                f.write(page_text + "\n")
                f.write("---PAGE DELIMITER---\n\n")
            else:
                f.write(f"Error fetching content from {link}\n\n")
            time.sleep(1)
    driver_content.quit()
    print(f"Scraping complete. Combined page content saved in {output_filename}.")

if __name__ == "__main__":
    main()
