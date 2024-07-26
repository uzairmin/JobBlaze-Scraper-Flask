from typing import List
import time
import pandas as pd
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from utils.helpers import configure_webdriver, loop_finish, upload_jobs_to_octagon, set_job_type
import urllib.parse


class DiceScraper:
    def __init__(self, driver, url, type) -> None:
        self.driver: WebDriver = driver
        self.url: str = url
        self.job_type: str = type
        self.scraped_jobs: List[dict] = []
        self.job: dict = {}
        self.errs: List[dict] = []

    @classmethod
    def call(cls, url, type):
        print("Running Dice...")
        try:
            driver: WebDriver = configure_webdriver()
            driver.maximize_window()

            dice_scraper: cls.__class__ = cls(
                driver=driver, url=url, type=type)
            dice_scraper.find_jobs()
        except Exception as e:
            print(e)

        print("Done Dice...")

    def find_jobs(self):
        original_window = self.driver.current_window_handle
        while True:
            parsed_url = urllib.parse.urlparse(self.url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            page_number = int(query_params.get("page", [1])[0])
            self.driver.get(self.url)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.TAG_NAME, "dhi-search-cards-widget"))
            )
            jobs = self.driver.find_elements(By.TAG_NAME, "dhi-search-card")

            # job_title = self.driver.find_elements(By.CLASS_NAME, "card-title-link")

            for job in jobs:
                self.driver.switch_to.window(original_window)
                # count += 1
                try:
                    job_title = job.find_element(
                        By.CLASS_NAME, "card-title-link")
                    self.job["job_title"] = job_title.text
                    c_name = job.find_element(
                        By.CLASS_NAME, "card-company"
                    ).find_element(By.TAG_NAME, "a")
                    self.job["company_name"] = c_name.text
                    address = job.find_element(
                        By.CLASS_NAME, "search-result-location")
                    self.job["job_source"] = "Dice"
                    self.job["job_type"] = set_job_type(
                        self.job_type)
                    self.job["address"] = address.text
                    original_window = self.driver.current_window_handle
                    job_title.click()
                    time.sleep(2)
                    self.driver.switch_to.window(
                        self.driver.window_handles[-1])
                    job_url = self.driver.current_url

                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located(
                                (By.CLASS_NAME, "job-description")
                            )
                        )
                        self.driver.find_element(
                            By.ID, "descriptionToggle").click()
                    except:
                        self.driver.close()
                        continue
                    job_description = self.driver.find_element(
                        By.CLASS_NAME, "job-description"
                    )
                    self.job["job_description"] = job_description.text
                    try:
                        job_posted_date = self.driver.find_element(
                            By.CLASS_NAME, "sc-dhi-time-ago"
                        )
                        self.job["job_posted_date"] = job_posted_date.text
                    except:
                        self.job["job_posted_date"] = "N/A"
                    self.job["job_source_url"] = job_url
                    self.job["job_description_tags"] = job_description.get_attribute(
                        "innerHTML"
                    )
                    self.job["salary_format"] = "N/A"
                    self.job["estimated_salary"] = "N/A"
                    self.job["salary_min"] = "N/A"
                    self.job["salary_max"] = "N/A"

                    self.scraped_jobs.append(self.job.copy())
                    self.job = {}
                    self.driver.close()
                    self.driver.switch_to.window(original_window)

                    time.sleep(0.5)
                except Exception as e:
                    print(e)
                time.sleep(1)

            self.upload_to_octagon()if len(self.scraped_jobs) > 0 else None
            self.scraped_jobs = []

            self.driver.switch_to.window(original_window)
            finished = "disabled"
            pagination = self.driver.find_elements(
                By.CLASS_NAME, "pagination-next")
            try:
                next_page = pagination[0].get_attribute("class")
                if finished in next_page:
                    break
                else:
                    query_params["page"] = [str(page_number + 1)]
                    new_query_string = urllib.parse.urlencode(
                        query_params, doseq=True)
                    self.url = urllib.parse.urlunparse(
                        parsed_url._replace(query=new_query_string)
                    )
                    time.sleep(5)
            except Exception as e:
                print(e)
                break
            self.upload_to_octagon()if len(self.scraped_jobs) > 0 else None
        self.driver.quit()

    def upload_to_octagon(self) -> None:
        upload_jobs_to_octagon({
            "jobs": self.scraped_jobs,
            "job_source": "dice"
        })


def dice(urls: list) -> None:
    for url in urls:
        DiceScraper.call(url=str(url.job_url), type=url.job_type)
    loop_finish("dice")
