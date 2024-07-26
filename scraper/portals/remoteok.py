from datetime import timedelta, datetime
from pytz import timezone
import pytz
from logging import exception
import sys
import traceback
from typing import List
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager



from utils.const import LINK_ISSUE, SCRAPING_ENDED
from utils.helpers import loop_finish, remove_emojis, configure_webdriver, set_job_type, upload_jobs_to_octagon


def load_jobs(driver):
    previous_len = len(driver.find_elements(
        By.CLASS_NAME, "company_and_position"))
    count = 0
    while True:
        if count == 5:
            break
        count += 1
        time.sleep(3)
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(5)
        elements = driver.find_elements(By.CLASS_NAME, "company_and_position")
        if previous_len == len(elements):
            break
        previous_len = len(elements)


def get_job_urls(driver):
    load_jobs(driver)
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "tr[data-slug][data-id]"))
        )
    except Exception as error:
        print(error)
    job_urls = driver.find_elements(By.CSS_SELECTOR, "tr[data-slug][data-id]")
    links = []
    for job_url in job_urls:
        try:
            if (check_if_job_week_ago(job_url)):
                link = job_url.get_attribute("data-href")
                links.append(link)
        except Exception as e:
            print(e)
    return links

def check_if_job_week_ago(job):
    week_ago = False
    try:
        date_elm = job.find_element(By.TAG_NAME, "time")
        date_str = date_elm.get_attribute("datetime")
        date_obj = datetime.fromisoformat(date_str).replace(tzinfo=pytz.utc)
        current_date = datetime.now(tz=pytz.utc)
        one_week_ago_date = current_date - timedelta(days=7)
        if date_obj >= one_week_ago_date:
            week_ago = True
    except Exception as e:
        print(e)
    return week_ago


def is_convertible_to_number(s):
    if isinstance(s, str):
        try:
            int(s)
            return True
        except ValueError:
            return False
    return False


def request_url(driver, url):
    driver.get(url)


def find_jobs(driver, job_type):
    scraped_jobs:List[dict] = []

    links = get_job_urls(driver)
    total_job = len(links)
    original_window = driver.current_window_handle
    for link in links:
        data: dict = {}
        if link:
            try:
                driver.switch_to.new_window('tab')
                driver.get("https://remoteok.com" + link)
                time.sleep(5)
                id = link.split("-")[-1]
                if is_convertible_to_number(id):
                    id = int(id)
                    job = WebDriverWait(driver, 40).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, f"job-{id}")))
                    job_desc = WebDriverWait(driver, 40).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "expandContents")))

                    temp = job.find_element(
                        By.CLASS_NAME, "company_and_position").text
                    temp = temp.splitlines()
                    job_title = remove_emojis(temp[0])
                    data["job_title"] = job_title

                    company_name = remove_emojis(temp[1])
                    data["company_name"] = company_name
                    data["job_source"] = "RemoteOk"
                    job_type = "full time"
                    sub_type = "remote"
                    data["job_type"] = set_job_type(job_type, sub_type)
                    address = 'Remote'
                    data["address"] = address

                    job_source_url = link

                    job_description = job_desc.text
                    data["job_description"] = job_description

                    temp1 = job.find_element(By.CLASS_NAME, "time").text
                    job_posted_date = temp1
                    data["job_posted_date"] = job_posted_date
                    data["job_source_url"] = job_source_url
                    job_description_tags = job_desc.get_attribute("innerHTML")
                    data["job_description_tags"] = str(job_description_tags)
                    salary_format = "yearly"
                    data["salary_format"] = salary_format
                    temp2 = temp[-1].split(" ")
                    if len(temp2[-3]) >= 4 and temp2[-3][0] == "$":
                        salary_min = remove_emojis(temp2[-3])
                    else:
                        salary_min = "N/A"

                    if len(temp2[-1]) >= 4 and temp2[-1][0] == "$":
                        salary_max = remove_emojis(temp2[-1])
                    else:
                        salary_max = "N/A"
                    if salary_max == "N/A" or salary_min == "N/A":
                        estimated_salary = "N/A"
                    else:
                        estimated_salary = f"{salary_min}-{salary_max}"
                    data["estimated_salary"] = estimated_salary
                    data["salary_min"] = salary_min
                    data["salary_max"] = salary_max

            except exception as e:
                print(e)
            
            driver.close()
            driver.switch_to.window(original_window)
            scraped_jobs.append(data.copy())

    status = upload_jobs_to_octagon({
            "jobs": scraped_jobs,
            "job_source": "remoteok"
        })
    return False, total_job

def remoteok(urls: list):
    print("Remote Ok")
    driver = configure_webdriver()
    try:
        driver.maximize_window()
        flag = True
        for url in urls:
            try:
                request_url(driver, str(url.job_url))
                while flag:
                    flag, _ = find_jobs(driver, url.job_type)
                    print("Fetching...")
                print(SCRAPING_ENDED)

            except Exception as e:
                print(LINK_ISSUE)

    except Exception as e:
        print(e)
    driver.quit()
    loop_finish("remoteok")