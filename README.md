# MonitorTrackingCoverage

**MonitorTrackingCoverage** is a Python script that allows you to compare to different states of tracking setups for web analytics for a given set of urls.

## Use Case ##

Imagine you have implemented **Adobe Data Collection** (vulgo: Adobe Launch) and you changed a data element or a rule. Before you want to publish the changes to production, you want to check, if the changes somehow harm the current setup, e.g. if the changes will change how dimensions will be tracked. This script records tracked dimensions from two different development environments to help you to find any issues like that.

It will read all tracked variables/dimensions from a given URL and a defined environment and puts the result to a JSON file. 

After that it will read all variables/dimensions for another environment but the same URL and compare the tracked variables/dimensions to the previous result. You will receive a JSOn file and an Excel sheet with all changes and an output to the screen. 

All files are placed in the subfolder **./results**.

This is an example of the ad hoc result of the test:

![Screenshot of ad hoc result](screenshots/adhoc_result.png?raw=true)

This is an example of the Excel result: 

![Screenshot of Excel result](screenshots/excel_result.png?raw=true)

## Prerequisites ##

This script uses the **Selenium** browser automation. It requires you to download the headless browser called "**Chrome driver**" from here: 

    https://chromedriver.chromium.org/downloads

The version of the required ChromeDrive must fit the version of the installed Chrome Browser on your system and, of course, your operating system. 

To get the version of your Chrome browser, either check "**chrome://version**" or run:  

    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

Put the downloaded into the script folder. 

On Mac Os you need to run the following command to remove the downloaded executable from quarantine: 

    xattr -d com.apple.quarantine chromedriver 

## Exemplary process ##

1. Prepare the settings.json and add a JSON-key that contains Adobe tracking URL as well as a set of pages. This example parses two pages only. Add as many as you want. The **container_before** key contains the URL of the tag container, that points to the **live environment** that holds your ideal setup. The key **container_after** points to e.g. your testing or **staging enviroment**, that you want to test:

        "example_setup": {
            "adobe_launch_host" : "assets.adobedtm.com",
            "adobe_analytics_host" : "customer.d3.sc.omtrdc.net",
            "container_before": "https://assets.adobedtm.com/launch-ABC123.min.js",
            "container_after": "https://assets.adobedtm.com/launch-ABC123-development.min.js",
            "urls" : {
                "Homepage": "https://example.com",
                "Searchresults": "https://example.com/search/q=keyword"
            }
        }

2. Run the script the first time in silent headless mode time to collect current status of tracked variables for the defined pages. The **env**-Argument points to the pages defined above. The **original**-Argument tells the script, where to put the results:

    ./run.py --mode=init --env=example_setup --original=original_2021-01-17.json --silent

3. Check the output from **original_2021-01-17.json** and if needed, adapt the conditions. The **value key **can hold a list of values, that you want to accept: 

        "value": ["1", "2", "3"],
        
The **required key** defines, if the variable is mandatory. Thats the default setting. Set it to fals to make the variable optional:

        "required" : false

The **length key** defines the length of the variable. Set it to -1 if you do not wish to control the length:

        "length": -1
   
1. Run the script the second time and set the **mode**-Argument to **test**. This mode will replace the tag-container-reference on every parsed page to point to the given tag-container in the settings.json, the one you want to test. It also creates a quick report showing what variables are missing. Finally it creates an Excel-Sheet that contains all variables for the tested pages. 

        ./run.py --mode=test --env=example_setup --original=original_2021-01-17.json --test=test_2021-01-17.json --silent


## Command Line Arguments ##

**--settings** (optional)

Points to the path + filename that contains the settings in JSON-format, see **Settings* section below.

**Default:** settings.json

**Example:**

    ./run.py --settings=settings.json


---
**--env** (mandatory)

Defines the section within the settings file, that contains the actual set of settings.

**Example:**

    ./run.py --env=example_setup

---
**--mode** (mandatory)

Defines the working mode of the script. Three modes are currently supported:

- **init**: initially read a state that later will be used as the "master template", the result will be saved to disc in JSON-format
- **test**: compare an initially read state with a current state, the result will be saved to disc in JSON-format
- **analyse**: reads the result of a previous test run and creates the analysis

**Example:**

    ./run.py --mode=init

---
**--original** (mandatory)

Defines the filename where the script should save the original state of tracking parameters. This parameter is mandatory at all times. If you run the script in init-mode, it's the destination where the tracked variables will be saved. If you run the script in test-mode, it's where the script reads the original state from.

**--test** (optional)

Defines the filename where the script should save the original state of tracking parameters. This parameter is optional, but you need to provide it in test-mode.

**Example:**

This will read the original tracked variables from **original_2021-01-01.json**  and then go through all given URL to get a current state of tracked variables. Those variables are being compared for every URL. The result will be written to **original_2021-02-04.json**.

    ./run.py --env=example_setup --original=original_2021-01-17.json --test=test_2021-02-04.json

**--silent** (optional)

If this parameter is given, the visual feedback will be surpressed - meaning you will not see the Chrome browser instance being opened (aka *headless mode*).

## Contribute ##

See How [to contribute](https://github.com/dbsystel/tracking-tester/blob/main/CONTRIBUTING.md)

## License ##

This project is licensed under [Apache-2.0](https://github.com/dbsystel/tracking-tester/blob/main/LICENSE)

Copyright 2023 DB Systel GmbH
