from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import pandas as pd
import time
import csv
import sys
import numpy as np
import re

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    ver = int(driver.capabilities['chrome']['chromedriverVersion'].split('.')[0])
    driver.quit()
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_argument("--disable-notifications")
    # disable location prompts & disable images loading
    prefs = {"profile.default_content_setting_values.geolocation": 1, "profile.managed_default_content_settings.images": 2, "profile.default_content_setting_values.cookies": 1}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = uc.Chrome(version_main = ver, options=chrome_options) 
    driver.set_window_size(1920, 1080)
    driver.maximize_window()
    driver.set_page_load_timeout(300)

    return driver


def scrape_classicshorts(path):

    start = time.time()
    print('-'*75)
    print('Scraping classicshorts.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()
    # initializing the dataframe
    data = pd.DataFrame()
    # if no books links provided then get the links
    if path == '':
        name = 'classicshorts_data.xlsx'
        # getting the books under each category
        links = []
        nbooks = 0
        homepages = ['https://www.classicshorts.com/abc/a-d.html', 'https://www.classicshorts.com/abc/e-h.html', 'https://www.classicshorts.com/abc/i-m.html', 'https://www.classicshorts.com/abc/n-s.html', 'https://www.classicshorts.com/abc/t-z.html']

        for homepage in homepages:
            driver.get(homepage)         
            # scraping books urls
            titles = wait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[class='storylisting']")))
            for title in titles:
                try:
                    text = title.get_attribute('onclick')
                    link = 'https://www.classicshorts.com'+ text.split("'")[1]
                    links.append(link)
                    nbooks += 1
                    print(f'Scraping the url for book {nbooks}')
                except Exception as err:
                    print('The below error occurred during the scraping from classicshorts.com, retrying ..')
                    print('-'*50)
                    print(err)
                    continue

        # saving the links to a csv file
        print('-'*75)
        print('Exporting links to a csv file ....')
        with open('classicshorts_links.csv', 'w', newline='\n', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Link'])
            for row in links:
                writer.writerow([row])

    scraped = []
    if path != '':
        df_links = pd.read_csv(path)
        name = path.split('\\')[-1][:-4]
        name = name + '_data.xlsx'
    else:
        df_links = pd.read_csv('classicshorts_links.csv')

    links = df_links['Link'].values.tolist()

    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass

    # scraping books details
    print('-'*75)
    print('Scraping Books Info...')
    print('-'*75)
    n = len(links)
    for i, link in enumerate(links):

        try:
            if link in scraped: continue
            driver.get(link)           
            details = {}
            print(f'Scraping the info for book {i+1}\{n}')

            # title and title link
            title_link, title = '', ''  
            title_link = link
            try:
                title = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[style='cursor:pointer; font-size:41px; font-style:italic; margin-bottom:35px; margin-top:30px; text-align:center; line-height:1.0;']"))).get_attribute('textContent').replace('\n', '').strip().title() 
            except:
                try:
                    title = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[style*='cursor:pointer; font-size:41px;']"))).get_attribute('textContent').replace('\n', '').strip().title()
                except:
                    print(f'Warning: failed to scrape the title for book: {link}')      
                    
            details['Title'] = title
            details['Title Link'] = title_link    
            
            # Author
            author, birth, death = '', '', ''
            try:
                text = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[style='font-weight:500;']"))).get_attribute('textContent')
                author = text.split('(')[0].strip()
                if '(' in text:
                    birth = text.split('(')[-1].split('-')[0].strip()
                    birth = int(re.findall("\d+", birth)[0]) 
                    death = text.split('(')[-1].split('-')[1][:-1].strip()
                    death = int(re.findall("\d+", death)[0]) 
            except:
                pass
                    
            details['Author'] = author                      
            details['Author Date of Birth'] = birth                      
            details['Author Date of Death'] = death                      

            # word count
            count = ''             
            try:
                count = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[style='font-size:15px; margin-bottom:40px;']"))).get_attribute('textContent').split(':')[-1].strip()
            except:
                print(f'Warning: failed to scrape the cat and genre for book: {link}')      
                
            details['Word Count'] = count

            # appending the output to the datafame        
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data ...')
                data.to_excel(name, index=False)
        except:
            pass

    # optional output to excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'classicshorts.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":

    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_classicshorts(path)

