import time

from typing import List
from selenium.webdriver.common.by import By
from utils.const import *
from utils.helpers import k_conversion, configure_webdriver, \
    set_job_type, upload_jobs_to_octagon


def request_url(driver, url):
    driver.get(url)

# find's job name
def find_jobs(driver, job_type):
    scraped_jobs:List[dict] = []
    time.sleep(3)
    jobs = driver.find_elements(By.CLASS_NAME, "slider_container")
    for job in jobs:
        try:
            data: dict = {}
            time.sleep(1)
            job.click()
            time.sleep(4)
            data["job_title"] = job.text.split('\n')[0]
            data["company_name"] = job.text.split('\n')[1]
            data["job_source"] = "Indeed"
            data["job_type"] = set_job_type(job_type)
            data["address"] = job.text.split('\n')[2]
            job_description = driver.find_element(
                By.CLASS_NAME, "jobsearch-jobDescriptionText")
            data["job_description"] = job_description.text
            data["job_source_url"] = driver.current_url
            job_posted_date = job.find_element(By.CLASS_NAME, "css-qvloho")
            try:
                data["job_posted_date"] = job_posted_date.text.split('\n')[1]
            except:
                data["job_posted_date"] = 'N/A'
            data["job_description_tags"] = job_description.get_attribute('innerHTML')
            try:
                estimated_salary = driver.find_element(By.CLASS_NAME, "css-19j1a75")
                if '$' in estimated_salary.text:
                    a_an = ''
                    if 'an' in estimated_salary.text:
                        a_an = 'an'
                    else:
                        a_an = 'a'
                    if 'hour' in estimated_salary.text.split(a_an)[1]:
                        data["salary_format"] = "hourly"
                    elif ('year' or 'annum') in estimated_salary.text.split(a_an)[1]:
                        data["salary_format"] = "yearly"
                    elif 'month' in estimated_salary.text.split(a_an)[1]:
                        data["salary_format"] = "monthly"
                    else:
                        data["salary_format"] = "N/A"
                    try:
                        data["estimated_salary"] = k_conversion(estimated_salary.text.split(a_an)[0])
                    except:
                        data["estimated_salary"] = "N/A"
                    try:
                        salary_min = estimated_salary.text.split('$')[1]
                        data["salary_min"] = k_conversion(salary_min.split(' ')[0])
                    except:
                        data["salary_min"] = "N/A"
                    try:
                        salary_max = estimated_salary.text.split('$')[2]
                        data["salary_max"] = k_conversion(salary_max.split(' ')[0])
                    except:
                        data["salary_max"] = "N/A"
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
            driver.back()
        except Exception as e:
            print(e)
    if len(scraped_jobs) > 0:
        status = upload_jobs_to_octagon({
            "jobs": scraped_jobs,
            "job_source": "indeed"
        })
        if not status:
            return False

    if not data_exists(driver):
        return False

    next_page = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Next Page']")
    next_page.click()
    return True


# check if there is more jobs available or not
def data_exists(driver):
    page_exists = driver.find_elements(By.CSS_SELECTOR, "a[aria-label='Next Page']")
    return False if len(page_exists) == 0 else True

# code starts from here
def indeed(urls:List):
    print("Indeed")
    for url in urls:
        try:
            driver = configure_webdriver()
            driver.maximize_window()
            # run_pia_proxy(driver)
            try:
                flag = True
                request_url(driver, str(url.job_url))
                time.sleep(5)
                while flag:
                    flag = find_jobs(driver, url.job_type)
                    print("Fetching...")
                print(SCRAPING_ENDED)
            except Exception as e:
                print(LINK_ISSUE)
            finally:
                driver.quit()
        except Exception as e:
            print(e)
        