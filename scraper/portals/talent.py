import time
from datetime import datetime
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from utils.const import *
from utils.helpers import configure_webdriver, loop_finish, set_job_type, upload_jobs_to_octagon


def request_url(driver, url):
    driver.get(url)


def find_jobs(driver, job_type):
    jobs = driver.find_elements(By.CLASS_NAME, "link-job-wrap")
    scraped_jobs:List[dict] = []
    for job in jobs:
        try:
            data: dict = {}
            time.sleep(1)
            job.click()
            time.sleep(3)

            job_title = driver.find_element(
                By.CLASS_NAME, "jobPreview__header--title")
            data["job_title"] = job_title.text
            company_name = driver.find_element(
                By.CLASS_NAME, "jobPreview__header--company")
            data["company_name"] = company_name.text
            data["job_source"] = "Talent"
            if 'remote' in job_type.lower():
                data["job_type"] = set_job_type(job_type)
            elif 'hybrid' in job_type.lower():
                data["job_type"] = set_job_type(job_type, 'hybrid')
            else:
                data["job_type"] = set_job_type(job_type, 'onsite')
            address = driver.find_element(
                By.CLASS_NAME, "jobPreview__header--location")
            data["address"] = address.text
            job_description = driver.find_element(
                By.CLASS_NAME, "jobPreview__body--description")
            data["job_description"] = job_description.text
            data["job_source_url"] = driver.current_url
            job_posted_date = driver.find_elements(
                By.CLASS_NAME, "c-card__jobDatePosted")
            if len(job_posted_date) > 0:
                data["job_posted_date"] = job_posted_date[0].text
            else:
                data["job_posted_date"] = 'Posted Today'
            data["job_source_url"] = driver.current_url

            data["job_description_tags"] = job_description.get_attribute('innerHTML')
            data["salary_format"] = "N/A"
            data["estimated_salary"] = "N/A"
            data["salary_min"] = "N/A"
            data["salary_max"] = "N/A"
            scraped_jobs.append(data.copy())
        except Exception as e:
            print(e)

    status = upload_jobs_to_octagon({
        "jobs": scraped_jobs,
        "job_source": "talent"
    })
    if not status:
        return False

    pagination = driver.find_elements(
        By.CLASS_NAME, "pagination")

    if len(pagination) == 0:
        return False
    else:
        next_page = pagination[0].find_elements(
            By.TAG_NAME, "a")
        try:
            next_page[-1].click()
            return True
        except Exception as e:
            return False


def talent(urls: list):
    print("Talent")
    for url in urls:
        try:
            driver = configure_webdriver()
            driver.maximize_window()
            flag = True
            try:
                request_url(driver, str(url.job_url))
                while flag:
                    flag = find_jobs(
                        driver, url.job_type)
                    print("Fetching...")
                print(SCRAPING_ENDED)
            except Exception as e:
                print(LINK_ISSUE)
            finally:
                driver.quit()

        except Exception as e:
            print(e)
    loop_finish("talent")