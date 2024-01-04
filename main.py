from selenium.webdriver.common import action_chains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver import Firefox, Chrome
from selenium import webdriver
from bs4 import BeautifulSoup
from typing import Any, List, Optional
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import pandas as pd
import csv
import requests 
import re

url = 'https://efdsearch.senate.gov/search/'

driver_path = 'geckodriver.exe'

browser = webdriver.Firefox()
browser.get(url)
wait = WebDriverWait(browser, 30)
wait2 = time.sleep(2)
data = pd.DataFrame(columns=["#", "Transaction Date", "Senator", "Owner", "Ticker", "Asset Name", "Asset Type", "Type", "Amount", "Comment", "URL"])

def next_page():
    try:
        wait2
        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="filedReports_next"]')))
        if 'disabled' in next_button.get_attribute('class'):
            print("DONE")
            return False
        else:
            next_button.click()
            print("NEXT PAGE")
            wait2
            filedReports_length = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="filedReports_length"]/label/select/option[4]')))
            filedReports_length.click()
            return True
    except TimeoutException:

        # If the "Next" button is not clickable, break the loop (we're on the last page)
        return False
    except StaleElementReferenceException:

        # If the "Next" button is stale, continue the loop (try again)
        return True

agree_statement = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#agree_statement')))
agree_statement.click()

periodic_transaction = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/main/div/div/div[5]/div/form/fieldset[3]/div/div/div/div[1]/div[2]/label/input')))
periodic_transaction.click()

searchForm = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="searchForm"]/div/button')))
searchForm.click()

filedReports_length = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="filedReports_length"]/label/select/option[4]')))
filedReports_length.click()

# Get all links on the page
while True:

    wait2
    links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'td a')))
    wait2

    # Loop through all links using a while loop and an index variable
    for index in range(len(links)):

        # Refetch the links to avoid StaleElementReferenceException
        wait2
        links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'td a')))
        wait2

        if index < len(links):
            try:
                link = links[index]

                # Loop through all links
                href = link.get_attribute('href')

                # Check if the link's href attribute contains "ptr"
                if "ptr" in href:

                    # Open link in a new tab
                    browser.execute_script("window.open(arguments[0], '_blank')", href)

                    # Switch to the new tab
                    browser.switch_to.window(browser.window_handles[-1])

                    # Wait
                    wait2

                    try:
                        # Wait for the table and name to appear
                        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'tbody'))) 

                        senator_name = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/div/div/div[2]/div[1]/h2')))

                        # Find all table rows
                        table_rows = table.find_elements(By.TAG_NAME, 'tr')

                        # Loop through each row
                        for row in table_rows:

                            # Extract text content from the row
                            row_cells = row.find_elements(By.TAG_NAME, 'td')

                            row_data = [cell.text for cell in row_cells]

                            if "Stock" in row_data or "NYSE" in row_data or "NASDAQ" in row_data:

                                row_dict = {
                                    "#": row_data[0],
                                    "Transaction Date": row_data[1],
                                    "Senator": senator_name.text,
                                    "Owner": row_data[2],
                                    "Ticker": row_data[3],
                                    "Asset Name": row_data[4],
                                    "Asset Type": row_data[5],
                                    "Type": row_data[6],
                                    "Amount": row_data[7],
                                    "Comment": row_data[8],
                                    "URL": href,
                                }

                                new_row = pd.DataFrame(row_dict, index=[0])

                                data = pd.concat([data, new_row], ignore_index=True)

                            else:
                                continue

                        # Close the new tab and switch back to the original tab
                        browser.close()

                        browser.switch_to.window(browser.window_handles[0])

                    except (TimeoutException, NoSuchElementException):
                        
                        # Print an error message if the table is not found
                        print(f"Table not found on page {href}")

                        # Close the new tab and switch back to the original tab
                        browser.close()

                        browser.switch_to.window(browser.window_handles[0])

                index += 1

            except StaleElementReferenceException:
                continue
        else:
            break

    if not next_page():
        break

# Save the DataFrame to a CSV file
data.to_csv("output.csv", index=False)

# Print the DataFrame to the console
print(data)

# Close the browser
browser.quit()