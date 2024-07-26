import re
import time
import traceback
from datetime import datetime
from typing import List, Union
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException, \
    ElementNotVisibleException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.helpers import configure_webdriver, loop_finish, make_plural, upload_jobs_to_octagon


class WeWorkRemotelyScraper:
    def __init__(self, driver, url) -> None:
        self.driver: WebDriver = driver
        self.url: str = url
        self.scraped_jobs: List[dict] = []
        self.job: dict = {}
        self.errs: List[dict] = []

    @classmethod
    def call(cls, url, type):
        print("Running We Work Remotely...", type)
        try:
            driver: WebDriver = configure_webdriver(open_browser=True)
            driver.maximize_window()
            wwr_scraper: cls.__class__ = cls(driver=driver, url=url)
            wwr_scraper.find_jobs()
        except Exception as e:
            print(e)

        print("Done We Work Remotely...")

    def request_page(self) -> None:
        try:
            self.driver.get(self.url)
        except Exception as e:
            self.handle_exception(e)

    def handle_exception(self, exception: Union[Exception, str]) -> None:
        traceback.format_exc()
        traceback_data = traceback.extract_tb(exception.__traceback__)
        if traceback_data and traceback_data[0]:
            self.errs.append({
                'scraper': 'weworkremotely',
                'file_path': traceback_data[0].filename or "",
                'line_number': traceback_data[0].lineno or "",
                'error_line': traceback_data[0].line or "",
                'from_function': traceback_data[0].name or ""
            })

    def get_element(self, locator: str, parent: WebElement = None, selector: str = 'class',
                    alls: bool = False) -> Union[WebElement, List[WebElement], None]:
        try:
            by: str = By.CLASS_NAME
            if selector == 'css':
                by: str = By.CSS_SELECTOR
            if selector == 'xpath':
                by: str = By.XPATH
            if selector == 'tag':
                by: str = By.TAG_NAME
            if selector == 'name':
                by: str = By.NAME  # For Input fields
            wait: WebDriverWait = WebDriverWait(parent or self.driver, 10)
            ec: EC = EC.presence_of_all_elements_located((by, locator)) if alls else EC.presence_of_element_located(
                (by, locator))
            return wait.until(ec)
        except (
                WebDriverException, TimeoutException, NoSuchElementException, ElementNotVisibleException,
                Exception) as e:
            self.handle_exception(e)
            return None

    def home_page_loaded(self) -> bool:
        loaded: bool = False
        for retry in range(1, 6):
            try:
                self.request_page()
                homepage_element: WebElement = self.get_element(
                    locator='jobs-container')
                if not homepage_element:
                    time.sleep(3)
                main_element: list[WebElement] = self.driver.find_elements(
                    By.CLASS_NAME, 'jobs')
                if main_element:
                    loaded = True
                    break
            except (WebDriverException, TimeoutException, NoSuchElementException, ElementNotVisibleException) as e:
                if retry < 5:
                    print(f"Retry {retry}/{5} due to: {e}")
                else:
                    self.handle_exception(e)
                    self.driver.quit()
                    break
        return loaded

    def extract_links(self) -> List[str]:
        job_links: list[str] = []
        if self.home_page_loaded():
            time.sleep(1)
            jobs_list: list[WebElement] = self.get_element(locator='section.jobs ul li:not(.view-all)', selector='css',
                                                           alls=True)
            for item in jobs_list:
                anchor_elements: list[WebElement] = self.get_element(selector='tag', locator='a', parent=item,
                                                                     alls=True)
                if anchor_elements and anchor_elements[1]:
                    job_links.append(anchor_elements[1].get_attribute('href'))
        return job_links

    def extract_salary(self, salary: str) -> None:
        pattern = r"\$(?P<min>[0-9,]+)(?:\s*-\s*\$(?P<max>[0-9,]+))?(\s+OR\s+MORE)?\s+(?P<format>[A-Z]+)"
        match = re.search(pattern, salary)
        if match:
            min_salary = match.group("min") or ""
            max_salary = match.group("max") or min_salary
            unit = match.group("format") or "USD"
            currency_format = "yearly" if int(
                max_salary.replace(',', '')) > 1000 else "monthly"
            self.job['salary_min'] = f"{min_salary}"
            self.job['salary_max'] = f"{max_salary}"
            self.job['salary_format'] = currency_format
            self.job['estimated_salary'] = f"{min_salary} - {max_salary} {unit}"
        else:
            self.job['salary_min'] = "N/A"
            self.job['salary_max'] = "N/A"
            self.job['salary_format'] = "N/A"
            self.job['estimated_salary'] = "N/A"

    def get_job_type(self, job_type: str) -> None:
        default_type: str = 'full time remote'
        if job_type == 'FULL-TIME':
            default_type: str = 'full time remote'
        if job_type == 'CONTRACT':
            default_type: str = 'contract remote'
        self.job['job_type'] = default_type

    @staticmethod
    def parse_posted_date(datetime_str: str) -> str:
        pattern = r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)$'
        match = re.match(pattern, datetime_str)
        if match:
            day_span = 24 * 60 * 60
            datetime_str = match.group(1)
            datetime_obj = datetime.strptime(
                datetime_str, "%Y-%m-%dT%H:%M:%SZ")
            current_time = datetime.now().replace(tzinfo=None)
            time_difference = (current_time - datetime_obj).total_seconds()
            days = time_difference // day_span
            # Remove days to get only hours or minutes
            time_difference = time_difference - days * day_span
            minutes = time_difference // 60
            hours = time_difference // (60 * 60)
            # Increment days if hours > 20
            if hours >= 20:
                days += 1
            if days == 0:
                if hours == 0:
                    result = f"{int(minutes)} {make_plural('minute', minutes)} ago"
                else:
                    result = f"{int(hours)} {make_plural('hour', hours)} ago"
            else:
                result = f"{int(days)} {make_plural('day', days)} ago"
        else:
            result = datetime_str
        return result

    def extract_values_from_header(self, header: Union[WebElement, None]) -> None:
        try:
            element: Union[WebElement, List[WebElement], None]
            if header:
                # Job Posted Date
                element: WebElement = self.get_element(locator='.listing-header-container time', selector='css',
                                                       parent=header)
                self.job['job_posted_date'] = self.parse_posted_date(
                    element.get_attribute('datetime'))
                # Job Title
                element: WebElement = self.get_element(locator='.listing-header-container h1', selector='css',
                                                       parent=header)
                self.job['job_title'] = element.text if element else "N/A"
                # Salary Details
                element: list[WebElement] = self.get_element(selector='css', locator='a span.listing-tag',
                                                             parent=header, alls=True)
                self.extract_salary(
                    element[-1].text if element and element[-1] else '')
                # Job Type
                self.get_job_type(
                    job_type=element[0].text if element and element[0] else '')
        except Exception as e:
            self.handle_exception(e)

    def extract_values_from_content(self, content: Union[WebElement, None]):
        try:
            if content:
                # Job Description with Tags
                self.job['job_description_tags'] = content.get_attribute(
                    'innerHTML') if content else "N/A"
                # Job Description without Tags
                self.job['job_description'] = content.text if content else "N/A"
        except Exception as e:
            self.handle_exception(e)

    def extract_values_from_company_section(self, company_section: Union[WebElement, None]):
        try:
            element: Union[WebElement, List[WebElement], None]
            if company_section:
                # Company Name & Address
                element: WebElement = self.get_element(
                    locator='h2', selector='tag', parent=company_section)
                self.job['company_name'] = element.text if element else "N/A"
                # Company Address
                element: WebElement = self.get_element(selector='css', locator='h3:not(.listing-pill)',
                                                       parent=company_section)
                self.job['address'] = element.text if element else "Remote"
        except Exception as e:
            self.handle_exception(e)

    def tab_visited(self) -> bool:
        try:
            header: WebElement = self.get_element(
                locator='/html/body/div[4]/div[2]/div[1]', selector='xpath')
            content: WebElement = self.get_element(
                locator='section.job div.listing-container', selector='css')
            company: WebElement = self.get_element(
                locator='/html/body/div[4]/div[2]/div[2]', selector='xpath')
            if header and company and content:
                time.sleep(1)
                self.extract_values_from_header(header=header)
                self.extract_values_from_content(content=content)
                self.extract_values_from_company_section(
                    company_section=company)
                job = self.job.copy()
                self.scraped_jobs.append(job)
                return True
            else:
                return False
        except WebDriverException as e:
            self.handle_exception(e)
            return False

    def find_jobs(self) -> None:
        try:
            urls: list[str] = self.extract_links()
            if len(urls) > 0:
                for url in urls[:2]:
                    try:
                        self.job['job_source_url'] = url
                        self.job['job_source'] = 'weworkremotely'
                        self.driver.get(url=url)
                        visited: bool = self.tab_visited()
                        if visited:
                            self.job.clear()
                        else:
                            continue
                    except Exception as e:
                        self.handle_exception(e)
                        continue
            self.driver.quit()
            self.upload_to_octagon()if len(self.scraped_jobs) > 0 else None
        except Exception as e:
            self.handle_exception(e)
            self.driver.quit()

    def upload_to_octagon(self) -> None:
        status = upload_jobs_to_octagon({
            "jobs": self.scraped_jobs,
            "job_source": "weworkremotely"
        })
        if not status:
            self.driver.quit()


def weworkremotely(urls: list) -> None:
    for url in urls:
        WeWorkRemotelyScraper.call(url=str(url.job_url), type=url.job_type)
    loop_finish("weworkremotely")