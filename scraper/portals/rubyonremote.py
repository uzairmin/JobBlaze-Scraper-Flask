from selenium.webdriver.common.by import By

from utils.helpers import k_conversion, configure_webdriver, loop_finish, set_job_type, \
    upload_jobs_to_octagon

from datetime import datetime, timedelta

total_job = 0
posted_date_max_checks = 3


# calls url
def request_url(driver, url):
    driver.get(url)


# append data for csv file
def append_data(data, field):
    data.append(str(field).strip("+"))


def extract_date(input_date, prefix="Published on "):
    if input_date.startswith(prefix):
        input_date = input_date[len(prefix):]
    return input_date


def is_one_week_ago(posted_date):
    try:
        current_date = datetime.now()
        one_week_ago_date = current_date - timedelta(days=7)
        converted_date = datetime.strptime(
            f"{posted_date} {current_date.year}", "%B %d %Y")
        return converted_date >= one_week_ago_date and converted_date <= current_date
    except ValueError:
        return False


def update_job_description(driver, data):
    current_url = driver.current_url
    try:
        for job in data:
            driver.get(job["job_source_url"])
            job_description = driver.find_elements(By.CLASS_NAME, "prose")[0]
            posted_date = driver.find_element(
                By.XPATH, "/html/body/section/section/main/section/div/div[1]/article/div[3]/h2")
            job["job_posted_date"] = extract_date(posted_date.text)
            job["job_description"] = job_description.text
            job["job_description_tags"] = str(
                job_description.get_attribute('innerHTML')
            )
    except Exception as e:
        print(e)
    driver.get(current_url)


# find's job name
def find_jobs(driver, job_type, total_job, link):
    try:
        request_url(driver, f'{link}')
        scrapped_data = []

        job_section = driver.find_elements(By.TAG_NAME, "ul")[4]

        jobs = job_section.find_elements(By.TAG_NAME, "li")

        salary_format = ""

        for job in jobs:

            data = {}

            if len(job.text.split("\n")) == 5:

                job_title, company_name, address, estimated_salary, job_posted_date = job.text.split(
                    "\n")

                if "k" in estimated_salary or "K" in estimated_salary:
                    salary_format = "Yearly"

                elif "year" in estimated_salary.lower():
                    salary_format = "Yearly"
                elif "hour" in estimated_salary.lower():
                    salary_format = "Hourly"
                elif "month" in estimated_salary.lower():
                    salary_format = "Monthly"

                estimated_salary = k_conversion(estimated_salary)

                salary_extrema = estimated_salary.split("-")
                min_salary = salary_extrema[0]
                max_salary = salary_extrema[1] if len(
                    salary_extrema) > 1 else min_salary

            elif len(job.text.split("\n")) == 4:
                # Character to search for
                char_to_find = "$"

                # Check if the character exists in any string
                found = any(char_to_find in s for s in job.text.split("\n"))

                if not found:
                    job_title, company_name, address, job_posted_date = job.text.split(
                        "\n")
                    salary_format = "N/A"
                    estimated_salary = "N/A"
                    min_salary = "N/A"
                    max_salary = "N/A"

            elif len(job.text.split("\n")) == 3:
                job_title, company_name, job_posted_date = job.text.split("\n")
                address = ""
                salary_format = "N/A"
                estimated_salary = "N/A"
                min_salary = "N/A"
                max_salary = "N/A"

            date_replica = any(replica in job_posted_date.lower()
                               for replica in ["featured", "new"])

            if date_replica or is_one_week_ago(job_posted_date):
                job_description = ""
                job_url = job.find_element(
                    By.TAG_NAME, "a").get_attribute("href")
                data["job_title"] = job_title
                data["company_name"] = company_name
                data["address"] = address if address else "Remote"
                data["job_description"] = job_description
                data["job_source_url"] = job_url
                data["job_posted_date"] = job_posted_date
                data["salary_format"] = salary_format
                data["estimated_salary"] = estimated_salary
                data["salary_max"] = min_salary
                data["salary_min"] = max_salary
                data["job_source"] = "Ruby On Remote"
                data["job_type"] = set_job_type(job_type)
                scrapped_data.append(data)
                total_job += 1
            else:
                global posted_date_max_checks
                posted_date_max_checks -= 1
                if posted_date_max_checks <= 0:
                    break
                else:
                    continue
        update_job_description(driver, scrapped_data)

        status = upload_jobs_to_octagon({
            "jobs": scrapped_data,
            "job_source": "rubyonremote"
        })

        # Stop for Link (No pagination then)
        if posted_date_max_checks <= 0 or not status:
            return False

        index = -1
        try:
            # pagination = driver.find_elements(By.CLASS_NAME, "paging")[0].find_elements(By.TAG_NAME, 'li')
            index = driver.find_elements(By.CLASS_NAME, "next")[
                0].get_attribute('class').find('disabled')
            if index != -1:
                return False
            else:
                return True
        except Exception as e:
            print(e)
            return False

    except Exception as e:
        print(e)
        print(f'scrapped stopped due to: {e}')
        return False


# code starts from here
def ruby_on_remote(urls):
    print("Ruby On Remote")
    for url in urls:
        print(f"URL: {url.job_url} || Type : {url.job_type}")
        link = str(url.job_url)
        base_link = link
        total_job = 0
        try:
            driver = configure_webdriver(block_media=True)
            driver.maximize_window()
            flag = True
            count = 0
            try:
                while flag:
                    if count != 0:
                        link = f'{base_link}?page={count + 1}'
                    flag = find_jobs(driver, url.job_type, total_job, link)
                    count = count + 1
                    print("Fetching...")
            except Exception as e:
                print(e)
            finally:
                driver.quit()

        except Exception as e:
            print(e)
    loop_finish("rubyonremote")

# link = "https://rubyonremote.com/remote-jobs-in-us/"
# job_type = "Remote"

# contract_remote = "https://rubyonremote.com/contract-remote-jobs/"
# ft_remote = "https://rubyonremote.com/full-time-remote-jobs/"
