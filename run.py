#!
# Copyright 2023 DB Systel GmbH
# License Apache-2.0

import time
from datetime import datetime # date time handling
import sys, os

# selenium
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumwire import webdriver  # wrapper to get network requests from browser and also modify LaunchRequests in real time (https://stackoverflow.com/questions/31354352/selenium-how-to-inject-execute-a-javascript-in-to-a-page-before-loading-executi)
from pathlib import Path # check if cookie dump exists
from urllib.parse import urlparse, parse_qs, urldefrag # extract get parameters from url

import argparse # to get runtime arguments

import pandas as pd # for export to Excel
import json # for export to JSON

from compare import Compare # small class to compare two dicts

from os import get_terminal_size # get available width in terminal output

# TODO: clean up unsued libs
# modify requests before rendering of page https://stackoverflow.com/questions/31354352/selenium-how-to-inject-execute-a-javascript-in-to-a-page-before-loading-executi
# from lxml import html
# from lxml.etree import ParserError
# from lxml.html import builder
#import pickle # to save / load cookies

def get_real_type(string: str) -> str:

    # TODO: also check if string is a date
    if is_int(string):
        return 'int'
    elif is_float(string):
        return 'float'
    else:
        return 'str'

def is_int(string: str) -> bool:
    try: 
        int(string)
        return True
    except ValueError:
        return False

def is_float(string: str) -> bool:
    try: 
        float(string)
        return True
    except ValueError:
        return False

class TrackTracker:
    """Compare two different states of tracked variables for a given set of webpages

    Keyword arguments:

    settings -- file that contains settings in JSON format

    env -- keyword that points to the section in the settings files to use

    mode -- init: initially read the original state, test: compare original state and current state, analyse: analyse test status and create a report

    original -- file that contains the original state in JSON format
    
    test -- file that contains the current state in JSON format

    silent -- set to true to enable headless mode, otherwise a browser window will open and you can "observe" the process
    
    focus -- set to a unique page name from your settings section to only scan this particular page, this will disable all file outputs to prevent unwanted loss of previous data
    """
    
    sitemap = {}
    url = None
    driver = None

    def __init__(self, 
        settings: str, 
        env: str, 
        mode: str, 
        original: str, 
        test: str,
        silent: str,
        focus: str = None):

        self.setup(settings, env, focus)

        # do not run in init mode when focus page is set
        # this would overwrite existing result file
        # which could be unexpected and hence unwanted

        if not os.path.exists('results'):
            os.makedirs(directory)
    
        if mode == 'init' and focus is None:

            self.init_driver(silent, mode)

            self.parse_pages(self.urls)

            self.identify_variables()

            with open('results/' + original, 'w') as file:
                json.dump(self.result, file)

            self.shutdown()

        elif mode == 'analyse':

            with open('results/' + test, 'r') as file:
                self.result = json.load(file)

            if focus is not None:
                self.result = {focus: self.result[focus]}

            self.analyse_result()

            # don't create the excel output when focus page is defined
            if focus is None:
                self.df_results_analysed.to_excel('results/' + test + '.xlsx')
                print(f'Wrote results to ./results/{test}.xlsx')

        elif mode == 'test':

            self.init_driver(silent, mode)

            self.parse_pages(self.urls)

            self.identify_variables()

            with open('results/' + original, 'r') as file:
                self.original = json.load(file)

            if focus is not None:
                self.original = {focus: self.original[focus]}

            compare = Compare()
            
            # TODO: add stop_on_error flag to stop on every error, makes it easier to fix errors
            self.result = compare.compare(self.result, self.var_mapping)

            # don't create the excel output when focus page is defined
            if focus is None:
                with open('results/' + test, 'w') as file:
                    json.dump(self.result, file)
                
            self.analyse_result()

            # don't create the excel output when focus page is defined
            if focus is None:
                self.df_results_analysed.to_excel('results/' + test + '.xlsx')
                print(f'Wrote results to ./results/{test}.xlsx')

            self.shutdown()

            # loop through given webpages to read the original (desired) status of a website

        # elif mode == 'test':
        #     # loop through given webpages to read the current status of a website
        #     # and compare it to the original status


        # TODO: parse result parameters and add type, length, required properties
        # "xyz": {
        #         "value": [1, 2, 3],
        #         "type": "int" | "float" | "str" | "*",
        #         "length": -1 | <LENGTH>,
        #         "required": true | false,
        #         "result": different_length
        #     },
            
        # if initial, just put result to file

    def switch_tag_container(self, request):

        if request.url == self.container_before:
            request.url = self.container_after

        return request

    def analyse_result(self):

        self.df_results_analysed = pd.DataFrame()

        all_variables = []

        # colored command line output        
        class bcolors:
            HEADER = '\033[95m'
            OKBLUE = '\033[94m'
            OKCYAN = '\033[96m'
            OKGREEN = '\033[92m'
            WARNING = '\033[93m'
            FAIL = '\033[91m'
            ENDC = '\033[0m'
            BOLD = '\033[1m'
            UNDERLINE = '\033[4m'

        terminal_width = get_terminal_size()[0] - 15

        print('\r\r')
        print(f'{bcolors.FAIL}{bcolors.BOLD}Test date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}{bcolors.ENDC}')
        print('\r\r')
        for page in self.result:

            print(f'\r{bcolors.FAIL}{bcolors.BOLD}{"░" * (terminal_width + 15)}{bcolors.ENDC}')
            print(f'{bcolors.OKGREEN}{bcolors.UNDERLINE}Results for "{page}"{bcolors.ENDC}:')
            print(f'URL: {self.result[page]["url"]}')

            for variable in self.result[page]['variables']:

                if variable not in all_variables:
                    all_variables.append(variable)

                # get available screen size to prevent wrapping, to make output more readable

                if 'error' in self.result[page]['variables'][variable] and self.result[page]['variables'][variable]['error'] == 1:
                    
                    print (f"\t {bcolors.OKCYAN}{variable}({self.result[page]['variables'][variable]['variable_mapping']}){bcolors.ENDC}:")

                    print (f"\t\t {bcolors.BOLD}message :{bcolors.ENDC} {self.result[page]['variables'][variable]['message']}")
                    print (f"\t\t {bcolors.BOLD}expected:{bcolors.ENDC} {', '.join(self.original[page]['variables'][variable]['value'])}"[:terminal_width])
                    print (f"\t\t {bcolors.BOLD}actual  :{bcolors.ENDC} {', '.join(self.result[page]['variables'][variable]['value'])}"[:terminal_width])
                    print ("\r")

        for page in self.result:

            values = []

            for variable in all_variables:
                if variable in self.result[page]['variables']:
                    values.append(self.result[page]['variables'][variable]['value'][0])
                else:
                    values.append('-')

            self.df_results_analysed[page] = values

        self.df_results_analysed.insert(0, 'variables', all_variables) 

    def parse_pages(self, pages):
        """Loop through a dict of pages. Expected format is:

            "page_name" : "url"

            page_name has to be unique, e.g.:

            "Startseite": "https://example.com/homepage",
            
            "Suchergebnisse": "https://example.com/searchresults/?q=keyword"

        """
        for page_name in pages:
            self.result[page_name] = self.parse_page(pages[page_name])

    def setup(self, settings, env, focus):

        with open(settings, 'r') as f:
            settings = json.load(f)
            f.close()
        
        settings = settings[env]

        self.urls = settings['urls']

        if focus is not None:
            self.urls = {focus: self.urls[focus]}

        self.adobe_analytics_host = settings['adobe_analytics_host']
        self.adobe_launch_host = settings['adobe_launch_host']
        self.result = {}
        self.original = {}
        self.container_before = settings['container_before']
        self.container_after = settings['container_after']
        self.grace_period = settings['grace_period']

        self.var_mapping = settings['mapping']

        if "cookies" in settings:
            self.cookies = settings['cookies']
        else:
            self.cookies = None

        # keep those for later use: automatically parse a whole website?
        # self.urls_parsed = [] # a plain list of all urls to parse
        # self.urls_to_parse_next = [] # a plain list of all urls to be parsed
        # self.internal_only = bool(settings['internal_only']) # parse links from same host
        # self.max_depth = settings['max_depth'] # from starting url, do not go deeper than this

    def init_driver(self, silent, mode):
        """
        Inits the chrome browser driver"""
        PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")

        caps = DesiredCapabilities.CHROME
        caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        caps["pageLoadStrategy"] = "normal"  # https://www.selenium.dev/documentation/en/webdriver/page_loading_strategy/

        # make chrome instance invisible
        options = webdriver.ChromeOptions()
        if silent:
            options.add_argument('headless')
            options.add_argument('window-size=200x200')
            options.add_argument("disable-gpu")

        self.driver = webdriver.Chrome(
            executable_path = DRIVER_BIN, 
            desired_capabilities = caps,
            chrome_options=options)

        # if mode is init, we do collect desired state of tracked variables, from the live
        # system, so we do not need to change the tag container from live to dev or staging:
        if mode != 'init':
            self.driver.request_interceptor = self.switch_tag_container

        # self.driver.header_overrides = {'Accept-Encoding': 'gzip'} # ensure we only get gzip encoded responses

    def shutdown(self):

        if self.driver is not None:
            self.driver.close()

    def identify_variables(self) -> dict:

        for page_name in self.result:

            current_page = self.result[page_name]

            for variable in current_page['variables']:
                current_value = current_page['variables'][variable]
                current_value_definition = {
                    'value': current_value,
                    'type': get_real_type(current_value[0]),
                    'length': len(current_value[0]),
                    'required': True
                }

                current_page['variables'][variable] = current_value_definition

            self.result[page_name] = current_page
            
    def parse_page(self, url) -> dict:

        result = {
            'url': url,
            'variables': {}
        }

        # TODO also record formulars, auto-fill forms and read attribute ACTION

        # TODO handle cookies
        # if Path("myfile.txt").exists(): 
        #     cookies = pickle.load(open("cookies.pkl", "rb"))
        #     print(cookies)
        #     for cookie in cookies:
        #         driver.add_cookie(cookie)


        # https://stackoverflow.com/a/63220249
        # this enables network tracking, this allows us to set cookies before the actual request
        # otherwise we could not place cookies in the websites domain
        self.driver.execute_cdp_cmd('Network.enable', {})
        
        # set cookies before actual request is made
        if self.cookies is not None:
            for cookie in self.cookies:
                self.driver.execute_cdp_cmd('Network.setCookie', {
                    'name' : cookie['name'], 
                    'value' : cookie['value'],
                    'domain' : cookie['domain']
                })

        # this enables network tracking
        self.driver.execute_cdp_cmd('Network.disable', {})

        self.driver.get(url)

        try:
            self.driver.wait_for_request(self.adobe_analytics_host, 1)
        except:
            
            # Access requests via the `requests` attribute
            for request in self.driver.requests:
                if request.response:
                    print(
                        request.url,
                        request.response.status_code,
                        request.response.headers['Content-Type']
                    )

            print(f'Could not find tracking container `{self.adobe_analytics_host}`on `{url}`, do you provided the correct container locations?')
            sys.exit()

        # grace period to give the onsite script time to work
        time.sleep(self.grace_period)

        #pickle.dump( driver.get_cookies() , open("cookies.pkl","wb"))

        for request in self.driver.requests:
            if request.response:
                if request.host == self.adobe_analytics_host:
                    if request.method == 'POST':
                        str_tracking_parameters = urlparse('https://dummy.dummy/dummy/?' + request.body.decode('utf-8'))
                    else:
                        str_tracking_parameters = urlparse(request.url)

                    dict_str_tracking_parameters = parse_qs(str_tracking_parameters.query, keep_blank_values=True)  
                    result['request_url'] = request.url

                    result['variables'] = dict_str_tracking_parameters

        # TODO: keep digital data for debuging purposes
        # digitalData = self.driver.execute_script("return digitalData;")

        return result

        # TODO: keep log output for debugging purposes
        # log = str([entry[u'message'] for entry in self.driver.get_log('browser')]).split('|')

        # TODO: automatically parse pages tree
        # elements = self.driver.find_elements_by_xpath("//a[@href]")
        # first get list of all links from the current page
        # for element in elements:
        #     # we have to separate both steps, otherwise you get:
        #     # Message: stale element reference: element is not attached to the page document
        #     # on this line
        #     url_full = element.get_attribute("href")
        #     # print(f'found {url_full}')
        #     next_url = urldefrag(url_full)[0]
        #     # print(f'cleaned to {next_url}')
        #     if (self.internal_only == True 
        #     and self.host == urlparse(url_full).hostname 
        #     and not next_url in self.urls_parsed 
        #     and not next_url in self.urls_to_parse_next):
        #         self.urls_to_parse_next.append(next_url)
        #         urls_from_this_level.append(next_url)
        
        # # then actually parse every given link, if not already done
        # for url_from_this_level in urls_from_this_level:
        #     self.parse_page(url_from_this_level, depth + 1)

if __name__ == '__main__':

    args_parser = argparse.ArgumentParser(
        
        description='Compare two different states of tracked variables.'

    )

    args_parser.add_argument('--settings', dest='settings', required=False, type=str, default='settings.json',
                        help='filename that contains the settings in JSON format')

    args_parser.add_argument('--env', dest='env', required=True, type=str, 
                        help='JSON key that points to the section in the settings files that contains the setup for the current process')

    args_parser.add_argument('--mode', dest='mode', required=False, type=str, default='test', choices=['test', 'init', 'analyse'], 
                        help='init: initially read the original state, test: compare original state and current state, analyse: analyse test status and create a report')

    args_parser.add_argument('--original', dest='original', required=True, type=str,
                        help='filename that contains original tracked variables in JSON format')

    args_parser.add_argument('--test', dest='test', required=False, type=str,
                        help='filename that contains current tracked variables in JSON format')

    args_parser.add_argument('--silent', dest='silent', required=False, action='store_true',
                        help='set parameter to enable headless mode, otherwise a browser window will open and you can "observe" the process')

    args_parser.add_argument('--focus', dest='focus', required=False, 
                        help='set to a unique page name from your settings section to only scan this particular page, this will disable all file outputs to prevent unwanted loss of previous data')

    args = args_parser.parse_args()

    # TODO: make "env" configurable 
    # run script like this: ./run.py -a=original_status -b=current_status
    # run script initially like this ./run.py -a=original_status
    # TODO: if current_status is not set or "init", create the original result file without comparison loop

    trackTracker = TrackTracker(
        args.settings, 
        args.env, 
        mode=args.mode,
        original = args.original,
        test = args.test,
        silent = args.silent,
        focus = args.focus
    )