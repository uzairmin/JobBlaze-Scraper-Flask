from logging import exception
import time

from selenium.webdriver.common.by import By

from utils.const import *
from utils.helpers import configure_webdriver, loop_finish, set_job_type, upload_jobs_to_octagon


def load_jobs(driver):
    previous_len = len(driver.find_elements(
        By.CLASS_NAME, "hxecsD"))
    print('loading jobs')
    while True:
        time.sleep(5)
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        elements = driver.find_elements(By.CLASS_NAME, "hxecsD")
        if previous_len == len(elements):
            break
        previous_len = len(elements)

    return elements


def get_job_urls(driver):
    job_urls = load_jobs(driver)
    links = []
    for job_url in job_urls:
        link = job_url.find_element(By.TAG_NAME, "a")
        t = job_url.find_element(
            By.CLASS_NAME, "new-job-item__JobItemDate-sc-1qa4r36-5")
        links.append([link.get_attribute("href"), t.text])
    return links


def request_url(driver, url):
    driver.get(url)


def find_jobs(driver, job_type):
    scrapped_data = []
    links = get_job_urls(driver)
    total_job = len(links)
    print(total_job)
    original_window = driver.current_window_handle
    for link in links:
        data = {}
        if link:
            try:
                driver.switch_to.new_window('tab')
                driver.get(link[0])
                time.sleep(5)
                temp = driver.find_element(
                    By.CLASS_NAME, "JpOdR")
                job_title = temp.find_element(
                    By.CLASS_NAME, "job-title__StyledJobTitle-sc-10irtcq-0")
                job_type_check = driver.find_elements(
                    By.CLASS_NAME, "job-meta__Wrapper-oh0pn7-0")[0].text.lower()

                data["job_title"] = job_title.text

                company_name = driver.find_element(
                    By.CLASS_NAME, "ktyJgG")
                
                data["company_name"] = company_name.text.splitlines()[0]

                data["address"] = 'Remote'

                data["job_source_url"] = link[0]

                data["job_description"] = temp.text

                data["job_posted_date"] = link[1]

                data["salary_format"] = "N/A"

                data["salary_min"] = "N/A"

                data["salary_max"] = "N/A"

                data["estimated_salary"] = 'N/A'

                data["job_source"] = "justremote"

                if 'contract' in job_type_check:
                    data["job_type"] = set_job_type('contract')
                elif 'permanent' in job_type_check:
                     data["job_type"] = set_job_type('full time')
                else:
                    continue

                data["job_description_tags"] = str(temp.get_attribute("innerHTML"))

            except exception as e:
                print(e)

            driver.close()
            driver.switch_to.window(original_window)
            scrapped_data.append(data)

    uploaded = upload_jobs_to_octagon({
        "jobs": scrapped_data,
        "job_source": "justremote"
    })
    if not uploaded:
        return False, total_job

    return False, total_job


# code starts from here
def just_remote(urls: list):
    print("Just Remote")
    for url in urls:
        print(f"URL: {url.job_url} || Type : {url.job_type}")
        try:
            driver = configure_webdriver()
            driver.maximize_window()
            flag = True
            try:
                request_url(driver, str(url.job_url))
                while flag:
                    flag, _ = find_jobs(driver, url.job_type)
                    print("Fetching...")
                print(SCRAPING_ENDED)
            except Exception as e:
                print(e)
                print(LINK_ISSUE)
            finally:
                driver.quit()

        except Exception as e:
            print(e)
    loop_finish("justremote")


# just_remote('https://justremote.co/remote-jobs', 'remote')
