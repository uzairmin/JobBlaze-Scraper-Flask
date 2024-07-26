import time
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.const import *
from utils.helpers import k_conversion, configure_webdriver, loop_finish, set_job_type, upload_jobs_to_octagon


def finding_job(driver, company_name, scraped_jobs):
    try:
        data: dict = {}
        loc_type = ''
        flag = True
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "bg-beige-lighter"))
        )
        job_title = driver.find_element(By.CLASS_NAME, "company-name").text
        data["job_title"] = job_title
        data["company_name"] = company_name
        data["job_source"] = "YCombinator"
        details = driver.find_elements(By.CLASS_NAME, "company-details")
        details_loc = details[1].find_elements(By.TAG_NAME, "div")
        address = details_loc[0].text
        if 'remote' in details[1].text.lower():
            loc_type = 'remote'
        elif 'hybrid' in details[1].text.lower():
            loc_type = 'hybrid'
        else:
            loc_type = 'onsite'
        job_type_check = details_loc[2].text
        if 'full-time' in job_type_check.lower():
            job_type = 'full time'
        elif 'contract' in job_type_check.lower():
            job_type = 'contract'
        else:
            flag = False
        data["job_type"] = set_job_type(job_type, loc_type)
        data["address"] = address
        description = driver.find_element(By.CLASS_NAME, "bg-beige-lighter")
        job_description = description.find_elements(By.TAG_NAME, "div")

        desc = ""
        desc_tags = ""
        for i in range(1, len(job_description)):
            desc += job_description[i].text
            desc_tags += job_description[i].get_attribute('innerHTML')
        data["job_description"] = desc
        data["job_posted_date"] = "N/A"
        data["job_source_url"] = driver.current_url
        data["job_description_tags"] = desc_tags
        salary = driver.find_element(By.CLASS_NAME, "company-title")
        slr = salary.find_elements(By.TAG_NAME, "div")
        if len(slr) > 0 and slr[0].text != '':
            estimated_salary = slr[0].find_element(By.TAG_NAME, "span").text
            if '-' in estimated_salary:
                salary_min = estimated_salary.split(' - ')[0]
                salary_max = estimated_salary.split(' - ')[1]
                salary_format = 'N/A'
            else:
                salary_min = estimated_salary.split('K')[0]
                salary_max = estimated_salary.split('K')[0]
                salary_format = 'N/A'
        else:
            salary_format = 'N/A'
            estimated_salary = 'N/A'
            salary_min = 'N/A'
            salary_max = 'N/A'
        data["salary_format"] = salary_format
        data["estimated_salary"] = k_conversion(estimated_salary)
        data["salary_min"] = k_conversion(salary_min)
        data["salary_max"] = k_conversion(salary_max)
        if flag:
            scraped_jobs.append(data.copy())
    except Exception as e:
        print(e)

def company_jobs(driver):
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "job-name"))
        )
        job_name = driver.find_elements(By.CLASS_NAME, "job-name")
        scraped_jobs: List[dict] = []
        for job in job_name:
            try:
                link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
                company_name = driver.find_element(By.CLASS_NAME, "company-name").text
                original_window = driver.current_window_handle
                driver.switch_to.new_window('tab')
                driver.get(link)
                finding_job(driver, company_name, scraped_jobs)
                driver.close()
                driver.switch_to.window(original_window)
            except Exception as e:
                print(e)
        status = upload_jobs_to_octagon({
            "jobs": scraped_jobs,
            "job_source": "ycombinator"
        })
    except Exception as e:
        print(e)

def loading(driver):
    while True:
        try:
            time.sleep(3)
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "loading"))
            )
            load = driver.find_elements(By.CLASS_NAME, "loading")
            if len(load) > 0:
                load[0].location_once_scrolled_into_view
            else:
                break
        except Exception as e:
            break

def login(driver):
    try:
        # WebDriverWait(driver, 60).until(
        #     EC.presence_of_element_located(
        #         (By.CLASS_NAME, "MuiTypography-root"))
        # )
        time.sleep(10)
        driver.find_element(By.CLASS_NAME, "MuiTypography-root").click()
        time.sleep(10)
        # WebDriverWait(driver, 60).until(
        #     EC.presence_of_element_located(
        #         (By.CLASS_NAME, "input-group"))
        # )
        driver.find_elements(By.CLASS_NAME, "input-group")[3].click()
        time.sleep(10)
        email = driver.find_elements(By.CLASS_NAME, "MuiInput-input")[3]
        email.clear()
        email.send_keys(Y_EMAIL)
        time.sleep(10)

        driver.find_elements(By.CLASS_NAME, "input-group")[4].click()
        time.sleep(10)
        password = driver.find_elements(By.CLASS_NAME, "MuiInput-input")[4]
        password.clear()
        password.send_keys(Y_PASSWORD)
        time.sleep(10)

        driver.find_element(By.CLASS_NAME, "sign-in-button").click()
        time.sleep(20)

        return True
    except Exception as e:
        return False


def request_url(driver, url):
    driver.get(url)

def find_jobs(driver):
    try:
        companies = driver.find_elements(By.CLASS_NAME, "text-2xl")
        for i in range(1, len(companies)):
            try:
                link = companies[i].find_elements(By.TAG_NAME, "a")[0].get_attribute('href')
                original_window = driver.current_window_handle
                driver.switch_to.new_window('tab')
                driver.get(link)
                company_jobs(driver)
                driver.close()
                driver.switch_to.window(original_window)
                passed = True
            except Exception as e:
                print(e)



    except Exception as e:
        print(e)


# code starts from here
def ycombinator(urls: list):
    print("YCombinator")
    for url in urls:
        try:
            driver = configure_webdriver()
            driver.maximize_window()
            try:
                request_url(driver, YCOMBINATOR_LOGIN_URL)
                driver.maximize_window()
                if login(driver):
                    request_url(driver, str(url.job_url))
                    loading(driver)
                    find_jobs(driver)
                else:
                    print("Login failed")
            except Exception as e:
                print(LINK_ISSUE)
            finally:
                driver.quit()
        except Exception as e:
            print(e)
    loop_finish("ycombinator")