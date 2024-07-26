import time
from tqdm import tqdm 
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.helpers import k_conversion, configure_webdriver, loop_finish, \
    set_job_type, is_cloudflare_captcha_exist, change_pia_location, generate_random_email, \
    upload_jobs_to_octagon


def submit_email_alert(driver):
    # submit modal for email notifcation
    form_submitted = False
    try:
        driver.find_element(By.NAME, "email_address").send_keys(
            generate_random_email())
        time.sleep(3)
        driver.find_element(By.CLASS_NAME, 'zrs_btn_primary_400').submit()
        time.sleep(3)
        form_submitted = True
    except Exception as e:
        handle_exception(e)
    if not form_submitted:
        try:
            driver.find_element(
                By.CLASS_NAME, 'text-button-primary-default-text').click()
        except Exception as e:
            handle_exception(e)
    time.sleep(3)


def get_job_url(job):
    return job.find_element(By.CLASS_NAME, "job_link").get_attribute('href')


def skip_verify_email_banner(driver):
    try:
        WebDriverWait(driver, 2).until(EC.presence_of_element_located(
            (By.CLASS_NAME, "auto_banner_close")))
        driver.find_element(By.CLASS_NAME, 'auto_banner_close').click()
    except Exception as e:
        handle_exception(e)


def skip_phone_input(driver):
    # skip the phone number dialog box
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div[data-testid="footer"]')))
        footer_divs = driver.find_elements(
            By.CSS_SELECTOR, 'div[data-testid="footer"]')
        for fdiv in footer_divs:
            try:
                fdiv.find_element(By.TAG_NAME, 'button').click()
                break
            except Exception as e:
                handle_exception(e)
    except Exception as e:
        handle_exception(e)


def get_job_detail(driver, job_source, job_url, job_type):
    try:
        WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.CLASS_NAME, "job_title")))
        skip_verify_email_banner(driver)
        job_title = driver.find_element(By.CLASS_NAME, "job_title").text
        company_name = driver.find_element(
            By.CLASS_NAME, "hiring_company").text
        job_description = driver.find_element(By.CLASS_NAME, "job_description")
        address = driver.find_element(By.CLASS_NAME, 'hiring_location').text

        job = {
            "job_title": job_title,
            "company_name": company_name,
            "address": address,
            "job_description": job_description.text,
            "job_source_url": job_url,
            "job_posted_date": 'N/A',
            "salary_format": "N/A",
            "estimated_salary": "N/A",
            "salary_min": "N/A",
            "salary_max": "N/A",
            "job_source": job_source,
            "job_type": set_job_type(job_type),
            "job_description_tags": job_description.get_attribute('innerHTML')
        }

        for single_job in driver.find_elements(By.XPATH, "//p[@class='job_more']"):
            if 'Posted date:' in single_job.text:
                job['job_posted_date'] = single_job.text
        try:
            job_est_sal = driver.find_element(
                By.CLASS_NAME, 't_compensation').text
            job['estimated_salary'] = k_conversion(
                job_est_sal.split(' per ')[0])
            job['salary_format'] = job_est_sal.split(' per ')[1]
            if 'year' in job['salary_format']:
                job['salary_format'] = 'yearly'
            elif 'hour' in job['salary_format']:
                job['salary_format'] = 'hourly'
            else:
                job['salary_format'] = 'N/A'
            try:
                job['salary_min'] = k_conversion(
                    job['estimated_salary'].split(' to ')[0])
            except:
                job['salary_min'] = 'N/A'
            try:
                job['salary_max'] = k_conversion(
                    job['estimated_salary'].split(' to ')[1])
            except:
                job['salary_max'] = 'N/A'

        except:
            job['estimated_salary'] = "N/A"
            job['salary_format'] = "N/A"
            job['salary_min'] = "N/A"
            job['salary_max'] = "N/A"
        return job, False
    except Exception as e:
        handle_exception(e)
        return None, True


def pagination_available(driver):
    try:
        driver.find_element(By.CLASS_NAME, 'load_more_btn')
        return False
    except Exception as e:
        handle_exception(e)
        return True


def find_jobs(driver, link, job_type):
    scrapped_data = []
    columns_name = ["job_title", "company_name", "address", "job_description", 'job_source_url', "job_posted_date",
                    "salary_format", "estimated_salary", "salary_min", "salary_max", "job_source", "job_type",
                    "job_description_tags"]
    try:
        submit_email_alert(driver)
        skip_phone_input(driver)
        time.sleep(4)
        driver.get(link)
        time.sleep(2)
        pagination_flag = pagination_available(driver)
        job_urls = []
        if pagination_flag:
            for i in range(30):
                try:
                    jobs = driver.find_elements(By.CLASS_NAME, 'group')
                    job_links = [job.find_element(
                        By.TAG_NAME, 'a').get_attribute('href') for job in jobs]
                    job_urls.extend(job_links)
                    next_page_link = driver.find_elements(By.CLASS_NAME, 'prev_next_page_btn')[
                        1].get_attribute('href')
                    skip_verify_email_banner(driver)
                    if driver.current_url != next_page_link:
                        driver.get(next_page_link)
                    else:
                        break
                except Exception as e:
                    handle_exception(e)
                    break
        else:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job_item")))
            try:
                time.sleep(6)
                jobs = []
                for i in range(25):
                    old_jobs_count = len(jobs)
                    jobs = driver.find_elements(By.CLASS_NAME, "job_item")
                    time.sleep(3)
                    if i == 0:
                        driver.find_element(
                            By.CLASS_NAME, 'load_more_btn').click()
                        time.sleep(5)
                    if len(jobs) > 2:
                        jobs[-1].location_once_scrolled_into_view
                        jobs[-2].location_once_scrolled_into_view
                    for job in jobs:
                        job.location_once_scrolled_into_view
                    time.sleep(5)
                    if old_jobs_count == len(jobs):
                        break
            except Exception as e:
                print('Loaded all jobs ...', e)

            jobs = driver.find_elements(By.CLASS_NAME, "job_item")
            job_urls = [get_job_url(job) for job in jobs]

        count = 0
        job_urls = list(
            filter(lambda link: 'https://www.ziprecruiter.com/k' in link, job_urls))
        total_jobs = len(job_urls)

        for job_url in tqdm(job_urls):
            try:
                driver.get(job_url)
                cloud_flare_error = False
                for i in range(5):
                    time.sleep(1)
                    cloud_flare_error = is_cloudflare_captcha_exist(driver)
                    if cloud_flare_error:
                        change_pia_location(driver)
                        driver.get(job_url)
                    else:
                        break
                if not cloud_flare_error:
                    job, error = get_job_detail(
                        driver, 'ziprecruiter', job_url, job_type)
                else:
                    error = True
                if not error:
                    data = [job[c] for c in columns_name]
                    scrapped_data.append(data)
                count += 1

                # upload jobs in chunks of 20 size
                if scrapped_data and count > 0 and (count % 20 == 0 or count == total_jobs - 1):
                    uploaded = upload_jobs_to_octagon({
                        "jobs": scrapped_data,
                        "job_source": "ziprecruiter"
                    })

                    if not uploaded:
                        driver.close()
                    scrapped_data = []

            except Exception as e:
                handle_exception(e)
                break
    except Exception as e:
        handle_exception(e)

def handle_exception(e):
    print(str(e))


def ziprecruiter(urls: list) -> None:
    print('Zip Recruiter')
    for url in urls:
        print(f"URL: {url.job_url} || Type : {url.job_type}")
        try:
            print("Start in try portion.\n")
            driver = configure_webdriver(
                block_media=True,
                block_elements=['css', 'img', 'cookies']
            )
            driver.maximize_window()
            try:
                driver.get(str(url.job_url))
                print("Fetching...")
                find_jobs(driver, str(url.job_url), url.job_type)
            except Exception as e:
                print("Error occurred during scraping. Details: ", e)
            finally:
                driver.close()
        except Exception as e:
            print("Error occurred. Details: ", e)
    
    loop_finish("ziprecruiter")
