import pandas as pd
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from utils.helpers import configure_webdriver, loop_finish, upload_jobs_to_octagon, set_job_type, k_conversion
import time


class SimplyHiredScraper:

    def __init__(self, driver, url, type) -> None:
        self.driver: WebDriver = driver
        self.url: str = url
        self.job_type: str = type
        self.scraped_jobs: List[dict] = []
        self.job: dict = {}
        self.errs: List[dict] = []

    @classmethod
    def call(cls, url, type):
        print("Running Simply Hired...")
        try:
            driver: WebDriver = configure_webdriver()
            driver.maximize_window()

            simply_hired_scraper: cls.__class__ = cls(
                driver=driver, url=url, type=type)
            simply_hired_scraper.driver.get(url)
            try:
                flag = True
                page_no = 2
                while flag and page_no <= 40:
                    flag = simply_hired_scraper.find_jobs(page_no)
                    page_no += 1
                    print("Fetching...")
                simply_hired_scraper.driver.quit()
            except Exception as e:
                print(e)
        except Exception as e:
            print(e)
        print("Done Simply Hired...")
        simply_hired_scraper.upload_to_octagon()if len(
            simply_hired_scraper.scraped_jobs) > 0 else None

    def upload_to_octagon(self) -> None:
        response = upload_jobs_to_octagon({
            "jobs": self.scraped_jobs,
            "job_source": "simplyhired"
        })

    def find_jobs(self, next_page_no):
        jobs = self.driver.find_elements(By.CLASS_NAME, "css-1igwmid")
        es = self.driver.find_elements(By.CLASS_NAME, "css-1ejkpji")
        count = 0

        for job in jobs:
            try:
                job.click()
                time.sleep(3)
                self.job["job_title"] = job.text
                context = self.driver.find_elements(
                    By.CLASS_NAME, "css-xyzzkl")
                company_name = context[0].text.split("-")[0]
                self.job["company_name"] = company_name
                self.job["job_source"] = "SimplyHired"
                self.job["job_type"] = set_job_type(
                    self.job_type)
                address = context[1].text
                self.job["address"] = address
                job_description = self.driver.find_elements(
                    By.CLASS_NAME, "css-1ebprri")[2]
                self.job["job_description"] = job_description.text
                job_url = job.find_element(
                    By.CSS_SELECTOR, "h2 > .css-1djbb1k").get_attribute("href")
                try:
                    job_posted_date = context[4].text
                except Exception as e:
                    job_posted_date = 'Today'
                self.job["job_posted_date"] = job_posted_date
                self.job["job_source_url"] = job_url
                self.job["job_description_tags"] = job_description.get_attribute(
                    'innerHTML')
                try:
                    estimated_salary = es[count].text.split(
                        " a")[0].replace('From', "")
                    if 'hour' in es[count].text:
                        self.job["salary_format"] = "hourly"
                    elif 'month' in es[count].text:
                        self.job["salary_format"] = "monthly"
                    elif 'year' in es[count].text:
                        self.job["salary_format"] = "yearly"
                    else:
                        self.job["salary_format"] = "N/A"
                    if "d: " in estimated_salary:
                        estimated_salary = estimated_salary.split(": ")[1]
                    if "to " in estimated_salary:
                        estimated_salary = estimated_salary.split("to ")[1]
                    self.job["estimated_salary"] = k_conversion(
                        estimated_salary)
                    try:
                        self.job["salary_min"] = k_conversion(
                            estimated_salary.split(' - ')[0])
                    except:
                        self.job["salary_min"] = "N/A"
                    try:
                        self.job["salary_max"] = k_conversion(
                            estimated_salary.split(' - ')[1])
                    except:
                        self.job["salary_max"] = "N/A"
                except:
                    self.job["salary_format"] = "N/A"
                    self.job["estimated_salary"] = "N/A"
                    self.job["salary_min"] = "N/A"
                    self.job["salary_max"] = "N/A"
                self.scraped_jobs.append(self.job.copy())
            except Exception as e:
                print(e)
            count += 1
        try:
            next_page = self.driver.find_elements(By.CLASS_NAME, "css-1vdegr")
            next_page_clicked = False
            for i in next_page:
                if i.text == f'{next_page_no}':
                    i.click()
                    time.sleep(3)
                    next_page_clicked = True
                    break
            return next_page_clicked
        except Exception as e:
            self.driver.quit()
            return False


def simplyhired(urls: list) -> None:
    for url in urls:
        SimplyHiredScraper.call(url=str(url.job_url), type=url.job_type)
    loop_finish("simplyhired")
