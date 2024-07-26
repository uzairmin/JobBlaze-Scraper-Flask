from utils.const import *
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
from utils.helpers import k_conversion, configure_webdriver, set_job_type, \
    run_pia_proxy, upload_jobs_to_octagon

total_job = 0


def handle_exception(e):
    print("Exception in linkedin => ", str(e))


# calls url
def request_url(driver, url):
    driver.get(url)


# login method
def login(driver, email, password):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
    except Exception as e:
        handle_exception(e)
        return False

    try:
        driver.find_element(By.ID, "username").click()
        driver.find_element(By.ID, "username").clear()
        driver.find_element(By.ID, "username").send_keys(email)

        driver.find_element(By.ID, "password").click()
        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(password)

        driver.find_element(By.CLASS_NAME, "btn__primary--large").click()
        not_logged_in = driver.find_elements(
            By.CLASS_NAME, "form__label--error")
        if len(not_logged_in) > 0:
            return False

        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "global-nav__primary-item"))
        )
        return True

    except Exception as e:
        handle_exception(e)
        return False

# find's job name


def find_jobs(driver, job_type, total_jobs, url=None):
    scrapped_data = []
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "jobs-search-results__list-item"))
        )
    except Exception as e:
        handle_exception(e)

    try:
        if url is not None:
            get_url = driver.current_url
            request_url(driver, get_url + str(url))
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "jobs-search-results__list-item"))
            )
    except Exception as e:
        handle_exception(e)
        return False, total_jobs

    time.sleep(2)
    if not data_exists(driver):
        return False, total_jobs

    jobs = driver.find_elements(
        By.CLASS_NAME, "jobs-search-results__list-item")

    for job in jobs:
        try:
            job.location_once_scrolled_into_view
        except Exception as e:
            handle_exception(e)

    jobs = driver.find_elements(
        By.CLASS_NAME, "jobs-search-results__list-item")

    address = driver.find_elements(
        By.CLASS_NAME, "artdeco-entity-lockup__caption")
    count = 0
    for job in jobs:
        try:
            data = {}
            job.click()

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "jobs-description-content__text"))
            )

            job_title = driver.find_element(
                By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title")
            data["job_title"] = job_title.text
            company_name = job.find_element(
                By.CLASS_NAME, "job-card-container__primary-description")
            data["company_name"] = company_name.text
            data["address"] = address[count].text

            job_description = driver.find_element(
                By.CLASS_NAME, "jobs-description-content__text")
            data["job_description"] = job_description.text

            job_source_url = driver.find_element(
                By.CLASS_NAME, "job-details-jobs-unified-top-card__content--two-pane")
            url = job_source_url.find_element(By.TAG_NAME, 'a')
            data["job_source_url"] = url.get_attribute('href')

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "tvm__text--positive"))
            )
            job_posted_date = driver.find_element(
                By.CLASS_NAME, "tvm__text--positive")
            job_date = job_posted_date.text.split('\n')[0]
            data["job_posted_date"] = job_date

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "job-details-jobs-unified-top-card__job-insight"))
            )

            try:
                estimated_salary = driver.find_elements(
                    By.CLASS_NAME, "job-details-jobs-unified-top-card__job-insight")[0].text
                if '$' in estimated_salary:
                    estimated_salary = estimated_salary.split('Full-time')[0]
                    estimated_salary = estimated_salary.split('Remote')[0]
                    try:
                        if 'yr' in estimated_salary:
                            data["salary_format"] = "yearly"
                        elif 'hr' in estimated_salary:
                            data["salary_format"] = "hourly"
                        else:
                            data["salary_format"] = "N/A"
                    except:
                        data["estimated_salary"] = "N/A"
                    try:
                        data["estimated_salary"] = k_conversion(
                            estimated_salary)
                    except:
                        data["estimated_salary"] = 'N/A'
                    try:
                        salary_min = estimated_salary.split('$')[1]
                        salary_min = salary_min.split(' ')[0]
                        data["salary_min"] = k_conversion(
                            salary_min.split('-')[0])
                    except:
                        data["salary_min"] = 'N/A'
                    try:
                        salary_max = estimated_salary.split('$')[2]
                        data["salary_max"] = k_conversion(
                            salary_max.split(' ')[0])
                    except:
                        data["salary_max"] = 'N/A'
                else:
                    data["salary_format"] = 'N/A'
                    data["estimated_salary"] = 'N/A'
                    data["salary_min"] = 'N/A'
                    data["salary_max"] = 'N/A'
            except:
                data["salary_format"] = 'N/A'
                data["estimated_salary"] = 'N/A'
                data["salary_min"] = 'N/A'
                data["salary_max"] = 'N/A'

            data["job_source"] = "Linkedin"
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "job-details-jobs-unified-top-card__job-insight"))
                )
                job_type_check = driver.find_element(
                    By.CLASS_NAME, "job-details-jobs-unified-top-card__job-insight")
                if 'Contract' in job_type_check.text:
                    data["job_type"] = set_job_type('Contract')
                elif 'Full-time' in job_type_check.text:
                    data["job_type"] = set_job_type('Full time')
                else:
                    data["job_type"] = set_job_type(job_type)
            except Exception as e:
                data["job_type"] = set_job_type(job_type)
                handle_exception(e)

            data["job_description_tags"] = job_description.get_attribute(
                'innerHTML')

            scrapped_data.append(data)

            total_jobs += 1
        except Exception as e:
            handle_exception(e)
        count += 1

    uploaded = upload_jobs_to_octagon({
        "jobs": scrapped_data,
        "job_source": "linkedin"
    })

    if not uploaded:
        return False, total_jobs

    return True, total_jobs


# check if there is more jobs available or not
def data_exists(driver):
    try:
        page_exists = driver.find_elements(
            By.CLASS_NAME, "jobs-search-no-results-banner__image"
        )
        return True if not page_exists and page_exists[0].text == '' else False
    except Exception as e:
        handle_exception(e)
        return True


def jobs_types(driver, url, job_type, total_job):
    count = 0
    request_url(driver, url)  # select type from the const file
    flag = True
    flag, total_job = find_jobs(driver, job_type, total_job)
    if flag:
        count += 25

        while flag:
            flag, total_job = find_jobs(
                driver, job_type, total_job, "&start=" + str(count))
            count += 25
    else:
        print(NO_JOB_RESULT)


# code starts from here
def linkedin(links: list) -> None:
    print("linkedin")
    total_job = 0
    for link in links:
        for x in LINKEDIN_ACCOUNTS:
            driver = configure_webdriver()
            driver.maximize_window()
            # run_pia_proxy(driver)
            try:
                request_url(driver, LOGIN_URL)
                logged_in = login(driver, x["email"], x["password"])
                try:
                    if logged_in:
                        jobs_types(driver, str(link.job_url),
                                   link.job_type, total_job)
                        break
                    else:
                        driver.quit()
                except Exception as e:
                    handle_exception(e)
                    driver.quit()
            except Exception as e:
                handle_exception(e)
                driver.quit()
                break
