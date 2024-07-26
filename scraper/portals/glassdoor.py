import time

import pandas as pd
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from app.models.accounts import Accounts
from utils.const import *
import app
from utils.helpers import k_conversion, configure_webdriver, loop_finish, \
    set_job_type, run_pia_proxy, upload_jobs_to_octagon\


def login(driver, email, password):
    try:
        time.sleep(2)
        driver.find_element(By.ID, "inlineUserEmail").click()
        driver.find_element(By.ID, "inlineUserEmail").clear()
        driver.find_element(By.ID, "inlineUserEmail").send_keys(email)
        btn = driver.find_element(By.CLASS_NAME, "emailButton")
        btn.find_element(By.TAG_NAME, "button").click()
        time.sleep(2)
        driver.find_element(By.ID, "inlineUserPassword").click()
        driver.find_element(By.ID, "inlineUserPassword").clear()
        driver.find_element(By.ID, "inlineUserPassword").send_keys(password)
        btn = driver.find_element(By.CLASS_NAME, "emailButton")
        btn.find_element(By.TAG_NAME, "button").click()
        time.sleep(5)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "button[name='submit']")))
            return True
        except Exception as e:
            return True
    except Exception as e:
        print(e)
        return False


def find_jobs(driver, job_type):
    scrapped_data:List[dict] = []
    uploaded = True
    columns_name = ["job_title", "company_name", "address", "job_description", 'job_source_url', "job_posted_date",
                    "salary_format", "estimated_salary", "salary_min", "salary_max", "job_source", "job_type",
                    "job_description_tags"]
    time.sleep(3)
    try:
        jobs = driver.find_elements(By.CLASS_NAME, "JobCard_jobCardWrapper__lyvNS")
        total_jobs = len(jobs)
        count = 0
        print(total_jobs)
        batch_size = 50
        for job in jobs:
            try:
                data: dict = {}
                job, error = get_job_detail(driver, job, job_type)
                if not error:
                    data = {c: job[c] for c in columns_name}
                    scrapped_data.append(data.copy())
                count += 1

                if scrapped_data and count > 0 and (count % batch_size == 0 or count == total_jobs - 1):
                    uploaded = upload_jobs_to_octagon({
                        "jobs": scrapped_data,
                        "job_source": "glassdoor"
                    })
                    if not uploaded:
                        return False
                    
                    scrapped_data = []
            except Exception as e:
                print(e)
                return False
    except Exception as e:
        print(e)
        return False
    return True


def get_job_detail(driver, jobs, job_type):
    try:
        jobs.click()
        time.sleep(3)
        job_detail = jobs.text.split('\n')
        job_title = jobs.find_element(
            By.CLASS_NAME, "JobCard_jobTitle___7I6y").text
        company_name = job_detail[0]
        address = jobs.find_element(
            By.CLASS_NAME, "JobCard_location__rCz3x").text

        job_url = jobs.find_element(
            By.CLASS_NAME, "JobCard_trackingLink__GrRYn").get_attribute('href')
        # click show more details for description
        try:
            driver.find_element(
                By.CLASS_NAME, "JobDetails_showMore___Le6L").click()
            time.sleep(0.5)
        except:
            pass
        job_description = driver.find_element(
            By.CLASS_NAME, "JobDetails_showHidden__C_FOA")

        try:
            job_posted_date = job_detail[-1]
        except:
            job_posted_date = "24h"

        job = {
            "job_title": job_title,
            "company_name": company_name,
            "address": address,
            "job_description": job_description.text,
            "job_source_url": job_url,
            "job_posted_date": job_posted_date,
            "salary_format": "N/A",
            "estimated_salary": "N/A",
            "salary_min": "N/A",
            "salary_max": "N/A",
            "job_source": "Glassdoor",
            "job_type": set_job_type(job_type, determine_job_sub_type(job_type)),
            "job_description_tags": job_description.get_attribute('innerHTML')
        }
        # find salary details
        try:
            estimated_salary = job_detail[3]
            if '$' in estimated_salary:
                es = estimated_salary.split(' (')[0]
                if 'Per' in es:
                    es_salary = es.split(" Per ")
                    salary_format = es_salary[1]
                    if 'Hour' in salary_format:
                        job["salary_format"] = "hourly"
                    elif 'Month' in salary_format:
                        job["salary_format"] = "monthly"
                    elif ('Year' or 'Annum') in salary_format:
                        job["salary_format"] = "yearly"
                else:
                    job["salary_format"] = "yearly"
                job["estimated_salary"] = k_conversion(es)
                if '-' in job["estimated_salary"]:
                    salary_range = job["estimated_salary"].split(" - ")
                    job["salary_min"] = salary_range[0].split(" Per")[0]
                    job["salary_max"] = salary_range[1].split(" Per")[0]
        except Exception as e:
            print(e)
        return job, False
    except Exception as e:
        return None, True

def determine_job_sub_type(type):
    sub_type = 'remote'
    if 'onsite' in type.lower() or 'on site' in type.lower():
        sub_type = 'onsite'
    if 'hybrid' in type.lower():
        sub_type = 'hybrid'
    return sub_type
    

def load_jobs(driver):
    try:
        time.sleep(3)
        driver.find_element(
            By.CSS_SELECTOR, "div.JobsList_wrapper__wgimi > div > button").click()
        return True
    except Exception as e:
        return False

def close_icon(driver):
    try:
        driver.find_element(By.CLASS_NAME, "modal_closeIcon").click()
    except:
        pass


def glassdoor(links):
    print("Glassdoor")
    for link in links:
        driver = configure_webdriver()
        try:
            driver.maximize_window()
            run_pia_proxy(driver)
            with app.app.app_context():
                accounts = Accounts.query.filter_by(source='glassdoor')
                for x in accounts:
                    driver.get(GLASSDOOR_LOGIN_URL)
                    logged_in = login(driver, x.email, x.password)
                    if logged_in:
                        break
            if logged_in:
                flag = True
                driver.get(str(link.job_url))
                close_icon(driver)
                pre = driver.find_elements(
                    By.CLASS_NAME, 'JobCard_jobCardContainer__l0svv')
                while flag:
                    flag = load_jobs(driver)
                    next = driver.find_elements(
                        By.CLASS_NAME, 'JobCard_jobCardContainer__l0svv')
                    if len(pre) == len(next):
                        break
                    else:
                        pre = next

                find_jobs(driver, link.job_type)
                print(SCRAPING_ENDED)
            else:
                print(LOGIN_FAILED)
        except Exception as e:
            print(e)
        driver.quit()
    loop_finish("glassdoor")


# glassdoor('https://www.glassdoor.com/Job/remote-aws-engineer-jobs-SRCH_IL.0,6_IS11047_KO7,19.htm?fromAge=3', '')
