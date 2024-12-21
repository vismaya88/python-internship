import time
import pickle
import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Initialize WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Chrome(options=options)
    return driver

# Save cookies after manual login
def save_cookies(driver, cookies_file):
    with open(cookies_file, "wb") as file:
        pickle.dump(driver.get_cookies(), file)

# Load cookies for authentication
def load_cookies(driver, cookies_file):
    with open(cookies_file, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)

# Manual login to Amazon
def login_amazon(driver):
    driver.get("https://www.amazon.in/")
    print("Please log in manually and complete any CAPTCHA if required.")
    input("Press Enter after logging in successfully...")
    save_cookies(driver, "amazon_cookies.pkl")

# Scrape a category
def scrape_category(driver, category_url, max_products=1500):
    driver.get(category_url)
    wait = WebDriverWait(driver, 10)
    products = []
    product_count = 0
    try:
        while product_count < max_products:
            time.sleep(3)
            items = driver.find_elements(By.CLASS_NAME, 'zg-item-immersion')

            for item in items:
                if product_count >= max_products:
                    break
                try:
                    name = item.find_element(By.CLASS_NAME, 'p13n-sc-truncate').text
                    price = item.find_element(By.CLASS_NAME, 'p13n-sc-price').text
                    rating = item.find_element(By.CLASS_NAME, 'a-icon-alt').text
                    num_reviews = item.find_element(By.CLASS_NAME, 'a-size-small').text
                    discount = "N/A"  # Placeholder: Modify logic to extract discounts
                    products.append({
                        "Product Name": name,
                        "Price": price,
                        "Rating": rating,
                        "Number of Reviews": num_reviews,
                        "Discount": discount
                    })
                    product_count += 1
                except NoSuchElementException:
                    continue

            # Navigate to the next page
            try:
                next_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'a-last')))
                next_button.click()
            except TimeoutException:
                print("No more pages available.")
                break
    except Exception as e:
        print(f"Error scraping category: {e}")
    return products

# Save data to CSV
def save_to_csv(data, filename):
    if data:
        keys = data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

# Save data to JSON
def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=4)

# Scrape categories using authenticated session
def scrape_authenticated_session(driver, category_url, max_products):
    products = scrape_category(driver, category_url, max_products)
    return products

# Main function
def main():
    driver = setup_driver()
    cookies_file = "amazon_cookies.pkl"
    try:
        # Check if cookies exist
        try:
            driver.get("https://www.amazon.in/")
            load_cookies(driver, cookies_file)
            driver.refresh()
            time.sleep(3)
            print("Cookies loaded. Authentication successful.")
        except Exception:
            print("No valid cookies found. Proceeding with manual login.")
            login_amazon(driver)

        # List of categories to scrape
        categories = [
            "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0",
            "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0",
            "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0",
            "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0",
            # Add more categories here
        ]

        all_products = []
        for category_url in categories:
            category_products = scrape_authenticated_session(driver, category_url, max_products=1500)
            all_products.extend(category_products)

        # Save data
        save_to_csv(all_products, "amazon_products.csv")
        save_to_json(all_products, "amazon_products.json")
        print("Data successfully saved!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
