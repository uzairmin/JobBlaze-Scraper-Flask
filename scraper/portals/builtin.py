import time
from typing import List
from selenium.webdriver.common.by import By
from utils.helpers import *

total_job = 0

# calls url
def request_url(driver, url):
    driver.get(url)

# find's job name
def find_jobs(driver, job_type):
    try:
        scrapped_data: List[dict] = []
        time.sleep(2)
        job_links = []
        links = driver.find_elements(By.CSS_SELECTOR, "a[data-id='view-job-button']")
        for link in links:
            job_links.append(link.get_attribute('href'))

        job_details = driver.find_elements(By.CLASS_NAME, "job-bounded-responsive")
        job_det = []
        for job in job_details:
            job_det.append(job.text)
        original_window = driver.current_url

        retries  = 5
        for i, url in enumerate(job_links):
            try:
                data: dict = {}
                job_detail = job_det[i].split('\n')
                data["job_title"] = job_detail[1]
                data["company_name"] = job_detail[0]
                data["job_source"] = "Builtin"
                data["job_posted_date"] = job_detail[2]
                # driver.switch_to.new_window('tab')
                driver.get(url)
                time.sleep(2)
                outer_loop_exit = False
                for retry in range(retries):
                    try:
                        driver.find_element(By.ID, "read-more-description-toggle").click()
                        # time.sleep(1)
                        break
                    except Exception as e:
                        if retry == retries:
                            outer_loop_exit = True
                            break
                        error_status = change_pia_location(driver)
                        if not error_status:
                            driver.get(url)
                        else:
                            outer_loop_exit = True
                            break
                if outer_loop_exit:
                    continue
                try:
                    address = driver.find_element(By.CLASS_NAME, "company-address").text
                except:
                    try:
                        address = driver.find_element(By.CLASS_NAME, "icon-description").text
                    except:
                        address = 'USA'
                data["address"] = address
                job_description = driver.find_element(By.CLASS_NAME, "job-description")
                data["job_description"] = job_description.text
                data["job_source_url"] = driver.current_url
                try:
                    estimated_salary = driver.find_element(By.CLASS_NAME, "provided-salary")
                    salary = estimated_salary.text
                    if 'hour' in salary:
                        data["salary_format"] = "hourly"
                    elif ('year' or 'annum' or 'Annually') in salary:
                        data["salary_format"] = "yearly"
                    elif 'month' in salary:
                        data["salary_format"] = "monthly"
                    else:
                        data["salary_format"] = "N/A"
                    try:
                        data["estimated_salary"] = k_conversion(salary.split(' A')[0])
                    except:
                        data["estimated_salary"] = "N/A"
                    try:
                        salary_min = salary.split('$')[1].split('-')[0]
                        data["salary_min"] = k_conversion(salary_min)
                    except:
                        data["salary_min"] = "N/A"
                    try:
                        salary_max = salary.split('$')[2].split(' A')[0]
                        data["salary_max"] = k_conversion(salary_max)
                    except:
                        data["salary_max"] = "N/A"
                except:
                    data["salary_format"] = "N/A"
                    data["estimated_salary"] = "N/A"
                    data["salary_min"] = "N/A"
                    data["salary_max"] = "N/A"
                try:
                    job_type_check = driver.find_element(By.CLASS_NAME, "company-info")
                    if 'remote' in job_type_check.text.lower():
                        data["job_type"] = set_job_type('Full time', 'remote')
                    elif 'hybrid' in job_type_check.text.lower():
                        data["job_type"] = set_job_type('Full time', 'hybrid')
                    else:
                        data["job_type"] = set_job_type('Full time', 'onsite')
                except Exception as e:
                    try:
                        job_type_check = driver.find_element(By.CLASS_NAME, "company-options")
                        if 'remote' in job_type_check.text.lower():
                            data["job_type"] = set_job_type('Full time', 'remote')
                        elif 'hybrid' in job_type_check.text.lower():
                            data["job_type"] = set_job_type('Full time', 'hybrid')
                        else:
                            data["job_type"] = set_job_type('Full time', 'onsite')
                    except Exception as e:
                        print(e)
                        data["job_type"] = set_job_type(job_type)
                data["job_description_tags"] = job_description.get_attribute('innerHTML')

                scrapped_data.append(data)
            except Exception as e:
                print(e)
            

            # switch_tab(driver, c, original_window)
        
        status = upload_jobs_to_octagon({
            "jobs": scrapped_data,
            "job_source": "builtin"
        })
        if not status:
            return False

        try:
            driver.get(original_window)
            time.sleep(2)
            next_page = driver.find_element(By.CLASS_NAME, 'pagination')
            pagination = next_page.find_elements(By.TAG_NAME, 'li')
            next_page_anchor = pagination[-1].find_element(By.TAG_NAME, 'a')
            next_page_url = next_page_anchor.get_attribute('href')
            driver.get(next_page_url)
            return True
        except Exception as e:
            return False
    except Exception as e:
        print(e)
        return False

# code starts from here
def builtin(links):
    print("Builtin")
    for link in links:
        driver = configure_webdriver(block_media=True, block_elements=['css', 'img'])
        try:
            driver.maximize_window()
            # run_pia_proxy(driver)
            try:
                flag = True
                request_url(driver, str(link.job_url))
                driver.maximize_window()
                while flag:
                    flag= find_jobs(driver, link.job_type)
            except Exception as e:
                print(e)
            finally:
                driver.quit()

        except Exception as e:
            print(e)
    loop_finish("builtin")
