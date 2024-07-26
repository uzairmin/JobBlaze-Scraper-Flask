import time
from datetime import datetime
import pandas as pd
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from utils.const import *
from utils.helpers import k_conversion, configure_webdriver, loop_finish, set_job_type, run_pia_proxy, upload_jobs_to_octagon


def load_jobs(driver):
    time.sleep(5)
    loading = "job-search-load-more"
    try:
        for load in driver.find_elements(By.CLASS_NAME, "sc-kdBSHD"):
            if loading in load.get_attribute("id"):
                return True
        return False

    except Exception as e:
        return False

# find's job name
def find_jobs(driver, job_type):
    scraped_jobs:List[dict] = []
    count = 0
    time.sleep(7)
    while load_jobs(driver):
        try:
            time.sleep(5)
            jobs = driver.find_elements(
                By.CLASS_NAME, "job-search-resultsstyle__JobCardWrap-sc-1wpt60k-4")
            for job in jobs:
                job.location_once_scrolled_into_view
        except Exception as e:
            print(e)
    jobs = driver.find_elements(
        By.CLASS_NAME, "job-search-resultsstyle__JobCardWrap-sc-1wpt60k-4")
    for job in jobs:
        try:
            
            data: dict = {}
            job.click()
            try: 
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "jobview-containerstyles__JobViewWrapper-sc-n3vjwx-0 fJluds"))
                )
            except:
                print("")
            job_title = driver.find_element(By.CLASS_NAME, "headerstyle__JobViewHeaderJobName-sc-onfits-9")
            data["job_title"] = job_title.text
            company_name = driver.find_element(By.CLASS_NAME, "headerstyle__JobViewHeaderCompanyName-sc-onfits-12")
            data["company_name"] = company_name.text
            data["job_source"] = "Monster"
            data["job_type"] = set_job_type(job_type)
            address = driver.find_element(By.CLASS_NAME, "headerstyle__JobViewHeaderDetails-sc-onfits-10").find_elements(By.TAG_NAME, "li")[1]
            data["address"] = address.text
            job_description = driver.find_element(By.CLASS_NAME, "descriptionstyles__DescriptionContainerOuter-sc-7dvtrp-0")
            data["job_description"] = job_description
            job_posted_date = driver.find_element(By.CLASS_NAME, "headerstyle__JobViewHeaderDetails-sc-onfits-10").find_elements(By.TAG_NAME, "li")[2]
            data["job_posted_date"] = job_posted_date
            url = driver.find_elements(
                By.CLASS_NAME, "sc-gAjuZT")
            data["job_source_url"] = url[count].get_attribute('href')
            count += 1
            data["job_description_tags"] = job_description.get_attribute('innerHTML')
            try:
                salary_string = driver.find_element(
                    By.CLASS_NAME, "detailsstyles__DetailsTableDetailBody-sc-1deoovj-5")
                if "$" in salary_string.text:
                    salary_format = "N/A"
                    estimated_salary = salary_string.text.split(" ")[0]
                    salary_min = salary_string.text.split("-")[0]
                    salary_max = salary_string.text.split("-")[1].split(" ")[0]
                    data["salary_format"] = salary_format
                    data["estimated_salary"] = k_conversion(estimated_salary)
                    data["salary_min"] = k_conversion(salary_min)
                    data["salary_max"] = k_conversion(salary_max)
                else:
                    data["salary_format"] = "N/A"
                    data["estimated_salary"] = "N/A"
                    data["salary_min"] = "N/A"
                    data["salary_max"] = "N/A"
            except:
                data["salary_format"] = "N/A"
                data["estimated_salary"] = "N/A"
                data["salary_min"] = "N/A"
                data["salary_max"] = "N/A"
            
            scraped_jobs.append(data.copy())
        except Exception as e:
            print("Exception in Monster => ", e)
    if len(scraped_jobs) > 0:
        status = upload_jobs_to_octagon({
            "jobs": scraped_jobs,
            "job_source": "monster"
        })

def monster(urls: list):
    print("Monster")
    try:
        for url in urls:
            driver = configure_webdriver()
            driver.maximize_window()
            try:
                run_pia_proxy(driver)
                time.sleep(10)
                driver.get(str(url.job_url))
                find_jobs(
                    driver, url.job_type)
                print("SCRAPING_ENDED")
            except Exception as e:
                print(LINK_ISSUE)
            finally:
                driver.quit()
    except Exception as e:
        print(e)
    loop_finish("monster")