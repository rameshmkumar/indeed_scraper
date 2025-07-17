#!/usr/bin/env python3

import time
import random
import json
import csv
import os
from datetime import datetime
import logging
from urllib.parse import urlencode, quote_plus
import pickle

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import undetected_chromedriver as uc

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IndeedScraper:
    
    COUNTRIES = {
        'AU': {'domain': 'au.indeed.com', 'name': 'Australia'},
        'IN': {'domain': 'in.indeed.com', 'name': 'India'},
        'US': {'domain': 'indeed.com', 'name': 'United States'},
        'UK': {'domain': 'uk.indeed.com', 'name': 'United Kingdom'},
        'CA': {'domain': 'ca.indeed.com', 'name': 'Canada'},
        'SG': {'domain': 'sg.indeed.com', 'name': 'Singapore'},
        'DE': {'domain': 'de.indeed.com', 'name': 'Germany'},
        'FR': {'domain': 'fr.indeed.com', 'name': 'France'}
    }
    
    DATE_FILTERS = {
        'any': '',
        'last_24_hours': '1',
        'last_3_days': '3',
        'last_7_days': '7',
        'last_14_days': '14',
        'last_30_days': '30'
    }
    
    def __init__(self, country='AU', save_session=True):
        if country not in self.COUNTRIES:
            raise ValueError(f"Country {country} not supported. Use: {list(self.COUNTRIES.keys())}")
        
        self.country = country
        self.base_url = f"https://{self.COUNTRIES[country]['domain']}"
        self.country_name = self.COUNTRIES[country]['name']
        self.save_session = save_session
        self.session_file = f"indeed_session_{country.lower()}.pkl"
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        logger.info(f"Setting up driver for Indeed {self.country_name}...")
        
        try:
            options = uc.ChromeOptions()
            options.add_argument('--no-first-run')
            options.add_argument('--no-service-autorun')
            options.add_argument('--password-store=basic')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-extensions')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            if self.save_session:
                user_data_dir = f"./chrome_session_{self.country.lower()}"
                options.add_argument(f'--user-data-dir={user_data_dir}')
                options.add_argument('--profile-directory=Default')
            
            self.driver = uc.Chrome(options=options, version_main=None)
            self.driver.implicitly_wait(10)
            
            if self.save_session and os.path.exists(self.session_file):
                self.load_session()
            
            logger.info(f"Driver setup complete for {self.country_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup driver: {e}")
            raise
    
    def save_session_data(self):
        if not self.save_session:
            return
        
        try:
            session_data = {
                'cookies': self.driver.get_cookies(),
                'current_url': self.driver.current_url,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)
            
            logger.info("Session saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def load_session(self):
        try:
            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)
            
            self.driver.get(self.base_url)
            time.sleep(2)
            
            for cookie in session_data['cookies']:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Could not add cookie: {e}")
            
            logger.info("Session loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
    
    def wait_for_cloudflare_challenge(self, timeout=120):
        print("Waiting for Cloudflare challenge to complete...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                page_source = self.driver.page_source.lower()
                current_url = self.driver.current_url.lower()
                
                cf_indicators = [
                    'cloudflare' in page_source,
                    'checking your browser' in page_source,
                    'additional verification required' in page_source,
                    'ray id' in page_source,
                    'cf-chl-widget' in page_source
                ]
                
                if any(cf_indicators):
                    print("Cloudflare challenge detected, waiting...")
                    time.sleep(3)
                    continue
                
                success_indicators = [
                    'jobs' in current_url,
                    'job' in page_source and 'company' in page_source,
                    'search results' in page_source
                ]
                
                if any(success_indicators):
                    print("Cloudflare challenge completed!")
                    return True
                
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"Error checking Cloudflare status: {e}")
                time.sleep(3)
                continue
        
        print("Timeout waiting for Cloudflare challenge")
        return False
    
    def build_search_url(self, job_title, location="", date_posted="any", salary_min=None, job_type=None):
        
        params = {
            'q': job_title,
            'l': location,
            'from': 'searchOnDesktopSerp'
        }
        
        if date_posted != "any" and date_posted in self.DATE_FILTERS:
            params['fromage'] = self.DATE_FILTERS[date_posted]
        
        if salary_min:
            params['salary'] = f"{salary_min}+"
        
        if job_type:
            params['jt'] = job_type
        
        params['vjk'] = 'e71ea2dbddfc21aa'
        
        query_string = urlencode(params, quote_via=quote_plus)
        search_url = f"{self.base_url}/jobs?{query_string}"
        
        return search_url
    
    def navigate_to_jobs(self, job_title, location="", date_posted="any", salary_min=None, job_type=None):
        
        search_url = self.build_search_url(job_title, location, date_posted, salary_min, job_type)
        
        print(f"Navigating to: {search_url}")
        print(f"Searching in: {self.country_name}")
        print(f"Date filter: {date_posted}")
        
        try:
            self.driver.get(search_url)
            time.sleep(3)
            
            if self.check_signin_required():
                print("Sign-in required. Please sign in manually...")
                self.wait_for_manual_signin()
            
            if self.wait_for_cloudflare_challenge():
                print("Successfully accessed job results!")
                self.save_session_data()
                return True
            else:
                print("Could not access job results")
                return False
                    
        except Exception as e:
            print(f"Error navigating to jobs: {e}")
            return False
    
    def check_signin_required(self):
        try:
            page_source = self.driver.page_source.lower()
            signin_indicators = [
                'sign in' in page_source,
                'login' in page_source,
                'authentication' in page_source,
                'verify' in page_source and 'human' in page_source
            ]
            
            return any(signin_indicators)
            
        except Exception as e:
            logger.error(f"Error checking sign-in requirement: {e}")
            return False
    
    def wait_for_manual_signin(self, timeout=300):
        print("Waiting for manual sign-in...")
        print("Please sign in manually in the browser window.")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url.lower()
                page_source = self.driver.page_source.lower()
                
                if 'jobs' in current_url and 'search' in page_source:
                    print("Sign-in successful!")
                    return True
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error waiting for sign-in: {e}")
                time.sleep(2)
                continue
        
        print("Timeout waiting for manual sign-in")
        return False
    
    def extract_detailed_job_info(self, job_element, retry_count=0):
        
        max_retries = 3
        
        try:
            title_selectors = [
                'h2 a[data-jk]',
                'h2 a',
                'a[data-jk]',
                '.jobTitle a',
                'a[href*="/viewjob"]',
                'h3 a',
                '[data-testid*="job-title"] a',
                'span[title] a'
            ]
            
            job_link = None
            for selector in title_selectors:
                try:
                    job_link = job_element.find_element(By.CSS_SELECTOR, selector)
                    if job_link and job_link.is_displayed():
                        break
                except NoSuchElementException:
                    continue
            
            if not job_link:
                print("Could not find clickable job link")
                return {}
            
            print("Clicking job for detailed info...")
            
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job_link)
                time.sleep(random.uniform(1, 2))
                
                try:
                    job_link.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", job_link)
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                if retry_count < max_retries:
                    print(f"Click failed, retrying... ({retry_count + 1}/{max_retries})")
                    time.sleep(2)
                    return self.extract_detailed_job_info(job_element, retry_count + 1)
                else:
                    print(f"Failed to click job after {max_retries} retries: {e}")
                    return {}
            
            detailed_info = {}
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            description_selectors = [
                '#jobDescriptionText',
                '.jobsearch-jobDescriptionText',
                '[data-testid="jobsearch-JobComponent-description"]',
                '.jobsearch-JobComponent-description',
                '.job-description',
                '.description',
                'div[class*="jobDescription"]',
                'div[class*="description"]'
            ]
            
            for selector in description_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    full_description = desc_elem.get_text(strip=True)
                    if full_description and len(full_description) > 100:
                        detailed_info['full_job_description'] = full_description
                        print(f"Full description extracted ({len(full_description)} chars)")
                        break
            
            profile_selectors = [
                '.jobsearch-CompanyInfoContainer',
                '.jobsearch-CompanyReview',
                '[data-testid="jobsearch-CompanyInfoContainer"]',
                '.company-profile',
                '.company-info',
                '.employer-info',
                'div[class*="company"]'
            ]
            
            for selector in profile_selectors:
                profile_elem = soup.select_one(selector)
                if profile_elem:
                    profile_text = profile_elem.get_text(strip=True)
                    if profile_text and len(profile_text) > 20:
                        detailed_info['profile_insights'] = profile_text
                        print(f"Profile insights extracted ({len(profile_text)} chars)")
                        break
            
            page_text = soup.get_text().lower()
            
            if 'employees' in page_text:
                lines = page_text.split('\n')
                for line in lines:
                    if 'employees' in line or 'employee' in line:
                        if any(char.isdigit() for char in line):
                            detailed_info['company_size'] = line.strip()
                            break
            
            benefits_keywords = ['benefits', 'health', 'insurance', 'vacation', 'pto', 'retirement']
            benefits_text = []
            lines = soup.get_text().split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in benefits_keywords):
                    if len(line.strip()) > 10:
                        benefits_text.append(line.strip())
                        if len(benefits_text) >= 5:
                            break
            
            if benefits_text:
                detailed_info['benefits'] = '; '.join(benefits_text)
            
            req_keywords = ['requirements', 'qualifications', 'skills', 'experience', 'education']
            req_text = []
            for line in lines:
                if any(keyword in line.lower() for keyword in req_keywords):
                    if len(line.strip()) > 20:
                        req_text.append(line.strip())
                        if len(req_text) >= 5:
                            break
            
            if req_text:
                detailed_info['job_requirements'] = '; '.join(req_text)
            
            print(f"Extracted {len(detailed_info)} detailed fields")
            return detailed_info
            
        except Exception as e:
            if retry_count < max_retries:
                print(f"Error extracting details, retrying... ({retry_count + 1}/{max_retries})")
                time.sleep(2)
                return self.extract_detailed_job_info(job_element, retry_count + 1)
            else:
                print(f"Failed to extract detailed info after {max_retries} retries: {e}")
                return {}
    
    def extract_jobs_from_page(self, page_num):
        print(f"Extracting jobs from page {page_num}...")
        
        jobs = []
        
        try:
            job_selectors = [
                '.job_seen_beacon',
                'div[data-jk]',
                '.jobsearch-SerpJobCard',
                '.result',
                'div[class*="job"]',
                'td[id*="job"]',
                'article[data-jk]',
                'li[data-jk]'
            ]
            
            job_elements = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_elements = elements
                        print(f"Found {len(elements)} job elements using: {selector}")
                        break
                except Exception as e:
                    continue
            
            if not job_elements:
                print("No job elements found")
                return jobs
            
            for i, element in enumerate(job_elements):
                try:
                    print(f"Processing job {i+1}/{len(job_elements)}")
                    
                    job_data = self.extract_basic_job_data(element)
                    
                    if job_data and job_data.get('title'):
                        job_data['position_on_page'] = i + 1
                        job_data['page_number'] = page_num
                        job_data['country'] = self.country_name
                        
                        detailed_info = self.extract_detailed_job_info(element)
                        job_data.update(detailed_info)
                        
                        jobs.append(job_data)
                        
                        print(f"Job {i+1}: {job_data.get('title', 'N/A')}")
                        print(f"   Company: {job_data.get('company', 'N/A')}")
                        print(f"   Location: {job_data.get('location', 'N/A')}")
                        
                        time.sleep(random.uniform(1, 3))
                        
                except Exception as e:
                    print(f"Error processing job {i+1}: {e}")
                    continue
            
            print(f"Successfully extracted {len(jobs)} jobs from page {page_num}")
            return jobs
            
        except Exception as e:
            print(f"Error during page extraction: {e}")
            return jobs
    
    def extract_basic_job_data(self, element):
        job_data = {}
        
        try:
            soup = BeautifulSoup(element.get_attribute('outerHTML'), 'html.parser')
            
            title_selectors = [
                'h2 a[data-jk]', 'h2 a', 'a[data-jk]', '.jobTitle a',
                'a[href*="/viewjob"]', 'h3 a', '[data-testid*="job-title"] a',
                'span[title] a', 'div[class*="title"] a'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title_text = title_elem.get('title', '') or title_elem.get_text(strip=True)
                    if title_text and len(title_text) > 2:
                        job_data['title'] = title_text
                        href = title_elem.get('href', '')
                        if href:
                            job_data['url'] = self.base_url + href if href.startswith('/') else href
                        job_data['job_id'] = title_elem.get('data-jk', '')
                        break
            
            company_selectors = [
                '.companyName a', '.companyName', 'span.companyName',
                '[data-testid*="company"] a', '[data-testid*="company"]',
                '.company a', '.company', 'div[class*="company"]'
            ]
            
            for selector in company_selectors:
                company_elem = soup.select_one(selector)
                if company_elem:
                    company_text = company_elem.get_text(strip=True)
                    if company_text and len(company_text) > 1:
                        job_data['company'] = company_text
                        break
            
            location_selectors = [
                '.companyLocation', '[data-testid*="location"]',
                '.locationsContainer', '.location', 'div[class*="location"]'
            ]
            
            for selector in location_selectors:
                location_elem = soup.select_one(selector)
                if location_elem:
                    location_text = location_elem.get_text(strip=True)
                    if location_text and len(location_text) > 1:
                        job_data['location'] = location_text
                        break
            
            salary_selectors = [
                '.salaryText', '[data-testid*="salary"]',
                '.salary-snippet', '.salary', 'div[class*="salary"]'
            ]
            
            for selector in salary_selectors:
                salary_elem = soup.select_one(selector)
                if salary_elem:
                    salary_text = salary_elem.get_text(strip=True)
                    if salary_text and any(char.isdigit() for char in salary_text):
                        job_data['salary'] = salary_text
                        break
            
            job_data['scraped_at'] = datetime.now().isoformat()
            job_data['source'] = f'Indeed {self.country_name}'
            job_data['scraper_method'] = 'Indeed Scraper'
            
            return job_data
            
        except Exception as e:
            print(f"Error extracting basic job data: {e}")
            return {}
    
    def check_for_more_pages(self):
        try:
            next_selectors = [
                'a[aria-label="Next Page"]',
                'a[aria-label="Next"]',
                'a[class*="next"]',
                'a[href*="start="]',
                'button[aria-label="Next"]'
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_displayed() and next_button.is_enabled():
                        return True, next_button
                except NoSuchElementException:
                    continue
            
            page_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="start="]')
            if page_elements:
                return True, None
            
            return False, None
            
        except Exception as e:
            print(f"Error checking for more pages: {e}")
            return False, None
    
    def go_to_next_page(self):
        print("Navigating to next page...")
        
        try:
            has_more, next_button = self.check_for_more_pages()
            
            if has_more and next_button:
                self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                time.sleep(random.uniform(1, 2))
                
                try:
                    next_button.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", next_button)
                
                time.sleep(random.uniform(3, 6))
                print("Successfully navigated to next page")
                return True
            else:
                print("No next page available")
                return False
                
        except Exception as e:
            print(f"Error navigating to next page: {e}")
            return False
    
    def scrape_all_pages(self, job_title, location="", date_posted="any", 
                        salary_min=None, job_type=None, max_pages=None):
        
        print(f"Starting scraping for Indeed {self.country_name}")
        print(f"Job: '{job_title}' | Location: '{location}' | Date: {date_posted}")
        
        all_jobs = []
        
        try:
            if not self.navigate_to_jobs(job_title, location, date_posted, salary_min, job_type):
                print("Could not access job results")
                return []
            
            page_num = 0
            consecutive_failures = 0
            
            while True:
                page_num += 1
                print(f"Processing page {page_num}")
                
                if max_pages and page_num > max_pages:
                    print(f"Reached maximum pages limit ({max_pages})")
                    break
                
                page_jobs = self.extract_jobs_from_page(page_num)
                
                if page_jobs:
                    all_jobs.extend(page_jobs)
                    print(f"Page {page_num}: {len(page_jobs)} jobs (Total: {len(all_jobs)})")
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= 3:
                        print("Too many consecutive failures - stopping")
                        break
                
                has_more_pages, _ = self.check_for_more_pages()
                if not has_more_pages:
                    print("No more pages - reached end")
                    break
                
                if not self.go_to_next_page():
                    print("Could not navigate to next page - stopping")
                    break
                
                time.sleep(random.uniform(2, 5))
                
                if page_num > 100:
                    print("Safety limit reached (100 pages)")
                    break
            
            print(f"SCRAPING COMPLETE!")
            print(f"Total pages: {page_num} | Total jobs: {len(all_jobs)}")
            
            self.save_session_data()
            
            return all_jobs
            
        except Exception as e:
            print(f"Critical error during scraping: {e}")
            return all_jobs
        
        finally:
            print("Keeping browser open for 10 seconds...")
            time.sleep(10)
    
    def save_results(self, jobs, job_title, location, date_posted):
        if not jobs:
            print("No jobs to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_location = "".join(c for c in location if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        filename_base = f"indeed_{self.country}_{safe_title}_{safe_location}_{date_posted}_{timestamp}"
        
        json_filename = f"{filename_base}.json"
        metadata = {
            "total_jobs": len(jobs),
            "scraped_at": datetime.now().isoformat(),
            "country": self.country_name,
            "source": f"Indeed {self.country_name}",
            "scraper": "Indeed Scraper",
            "search_params": {
                "job_title": job_title,
                "location": location,
                "date_posted": date_posted
            }
        }
        
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({"metadata": metadata, "jobs": jobs}, f, indent=2, ensure_ascii=False)
        
        csv_filename = f"{filename_base}.csv"
        if jobs:
            fieldnames = set()
            for job in jobs:
                fieldnames.update(job.keys())
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
                writer.writeheader()
                writer.writerows(jobs)
        
        print(f"RESULTS SAVED:")
        print(f"   JSON: {json_filename}")
        print(f"   CSV: {csv_filename}")
        
        return json_filename, csv_filename
    
    def cleanup(self):
        if self.driver:
            self.driver.quit()
            print("Browser closed")

def main():
    print("Indeed Scraper")
    print("=" * 40)
    
    COUNTRY = 'IN'
    JOB_TITLE = "data engineer"
    LOCATION = "india"
    DATE_POSTED = "last_14_days"
    
    print(f"Country: {COUNTRY}")
    print(f"Job Title: {JOB_TITLE}")
    print(f"Location: {LOCATION}")
    print(f"Date Filter: {DATE_POSTED}")
    print("=" * 40)
    
    scraper = IndeedScraper(country=COUNTRY, save_session=True)
    
    try:
        jobs = scraper.scrape_all_pages(
            job_title=JOB_TITLE,
            location=LOCATION,
            date_posted=DATE_POSTED,
            max_pages=None
        )
        
        if jobs:
            print(f"SUCCESS! Scraped {len(jobs)} jobs")
            
            json_file, csv_file = scraper.save_results(jobs, JOB_TITLE, LOCATION, DATE_POSTED)
            
            with_desc = len([j for j in jobs if j.get('full_job_description')])
            with_insights = len([j for j in jobs if j.get('profile_insights')])
            
            print(f"STATISTICS:")
            print(f"   Total jobs: {len(jobs)}")
            print(f"   With full descriptions: {with_desc}")
            print(f"   With profile insights: {with_insights}")
            print(f"   Success rate: {(with_desc/len(jobs)*100):.1f}%")
            
        else:
            print("No jobs scraped")
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()