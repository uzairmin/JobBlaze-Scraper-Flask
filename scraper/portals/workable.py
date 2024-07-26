from tqdm import tqdm
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.const import *
from utils.helpers import configure_webdriver, loop_finish, set_job_type, upload_jobs_to_octagon

total_job = 0

# calls url


def request_url(driver, url):
    driver.get(url)

# loading jobs
def loading(driver, count):
    try:
        time.sleep(3)
        load = driver.find_element(
            By.CLASS_NAME, "jobsList__button-container--3FEJ-")
        btn = load.find_element(By.TAG_NAME, "button")
        btn.location_once_scrolled_into_view
        btn.click()
        count += 1
        if count == 30:
            return False, count
        return True, count
    except Exception as e:
        return False, count


# click accept cookie modal
def accept_cookie(driver):
    try:
        driver.find_element(
            By.CLASS_NAME, "styles__accept-button--1eW01").click()
    except Exception as e:
        print(e)


def find_job_link(job):
    return job.find_element(By.TAG_NAME, "a").get_attribute("href")

# find's job


def find_jobs(driver, job_type):
    try:
        scrapped_data = []
        count = 0
        time.sleep(3)
        jobs = driver.find_elements(
            By.CLASS_NAME, "jobsList__list-item--3HLIF")
        job_urls = [find_job_link(job) for job in jobs]
        print('total jobs', len(jobs))
        for url in tqdm(job_urls[:4]):
            try:
                data = []
                driver.get(url)

                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "jobBreakdown__job-breakdown--31MGR"))
                )
                job_title = driver.find_element(
                    By.CLASS_NAME, "jobOverview__job-title--kuTAQ")
                data["job_title"] = job_title.text
                company_name = driver.find_element(
                    By.CLASS_NAME, "companyName__link--2ntbf")
                data["company_name"] = company_name.text
                address = driver.find_elements(
                    By.CLASS_NAME, "jobDetails__job-detail--3As6F")[1]
                data["address"] = address.text
                job_description = driver.find_element(
                    By.CLASS_NAME, "jobBreakdown__job-breakdown--31MGR")
                data["job_description"] = job_description.text
                data["job_source_url"] = driver.current_url
                job_posted_date = driver.find_element(
                    By.CLASS_NAME, "jobOverview__date-posted-container--9wC0t")
                data["job_posted_date"] = job_posted_date.text
                data["salary_format"] = "N/A"
                data["estimated_salary"] = "N/A"
                data["salary_min"] = "N/A"
                data["salary_max"] = "N/A"
                data["job_source"] = "Workable"
                try:
                    job_type_check = driver.find_element(
                        By.CLASS_NAME, "jobOverview__job-details--3JOit")
                    if 'contract' in job_type_check.text.lower():
                        data["job_type"] = set_job_type(
                            'Contract', determine_job_sub_type(job_type_check.text))
                    elif 'full time' in job_type_check.text.lower():
                        data["job_type"] = set_job_type(
                            'Full time', determine_job_sub_type(job_type_check.text))
                    else:
                        data["job_type"] = set_job_type(job_type)
                except Exception as e:
                    print(e)
                    data["job_type"] = set_job_type(job_type)
                data["job_description_tags"] = job_description.get_attribute('innerHTML')
                scrapped_data.append(data)
                count += 1
            except Exception as e:
                print(str(e))

        if len(scrapped_data) > 0:
            uploaded = upload_jobs_to_octagon({
                "jobs": scrapped_data,
                "job_source": "workable"
            })
            if not uploaded:
                print("Failed to upload jobs to octagon")
                driver.close()
                return False

        return True
    except Exception as e:
        print(str(e))
        return False


def determine_job_sub_type(type):
    sub_type = 'onsite'
    if 'remote' in type.lower():
        sub_type = 'remote'
    if 'hybrid' in type.lower():
        sub_type = 'hybrid'
    return sub_type


# code starts from here
def workable(links: list):
    print("Workable")
    for link in links:
        print(f"URL: {link.job_url} || Type : {link.job_type}")
        driver = configure_webdriver(block_media=True, block_elements=['img'])
        try:
            driver.maximize_window()
            try:
                flag = True
                request_url(driver, str(link.job_url))
                driver.maximize_window()
                accept_cookie(driver)
                count = 0
                while flag:
                    flag, count = loading(driver, count)
                if find_jobs(driver, link.job_type):
                    print(SCRAPING_ENDED)
                else:
                    print(ERROR_TEXT)
            except Exception as e:
                print(str(e))
                print(LINK_ISSUE)
        except Exception as e:
            print(str(e))
        driver.quit()
    loop_finish("workable")
