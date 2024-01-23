# Copyright 2023 DB Systel GmbH
# License Apache-2.0

from email import message
from os import error

from importlib_metadata import abc

# This class parses JSON objects and compares variables in the predefined format.
#
# {
#     "ID": {
#         "variables": {
#             "var_name": {
#                 "value": [ 1, 2, 3 ],
#                 "type": "int" | "float" | "str" | "*",
#                 "length": -1 | <LENGTH>,
#                 "required": true | false,
#                 "error": 0 | 1,
#                 "message": <RESULT>
#             },
#         }
#     }
# }
#

class Compare():
    
    target_key = "variables"
    pages: dict = {}

    def __init__(self, pages: dict) -> None:

        self.pages = pages

    # Checks the passed JSON object for the correct format and 
    # then if the passed values match what is expected from 
    # the original JSON.
    def compare(self, pages_before, pages_after) -> dict:
        
        obj_result = pages_before.copy()

        self.succeed = 0
        self.failed = 0

        # loop through the pages
        for original_page in self.pages:
            
            if original_page not in pages_before:
                raise error("Execution stopped! Page '" + str(original_page) + "' was not found in the JSON object.")
                # or use continue for ignore the missing pages

            original_variables = self.pages[original_page][self.keyword]
            # loop through the adobe analytics variables
            for original_variable in original_variables:
                
                original_variable_def = original_variables[original_variable]

                # check if the variable exists in the JSON
                if original_variable not in pages_before[original_page][self.keyword]:
                    
                    self.failed += 1

                    obj_result[original_page][self.keyword][original_variable] = {
                        "value": [""],
                        "message": "Test failed. Variable was not found in the list of variables.",
                        "error": 1
                    }

                    if original_variable in pages_after:
                        obj_result[original_page][self.keyword][original_variable]['variable_mapping'] = pages_after[original_variable]
                    else:
                        obj_result[original_page][self.keyword][original_variable]['variable_mapping'] = '-'

                    continue

                tested_variable_result = obj_result[original_page][self.keyword][original_variable]

                if original_variable in pages_after:
                    tested_variable_result['variable_mapping'] = pages_after[original_variable]
                else:
                    tested_variable_result['variable_mapping'] = '-'
                
                tested_variable = pages_before[original_page][self.keyword][original_variable]

                # if dict, then check the entries in the dictionary
                if type(tested_variable) is not dict:
                    tested_variable_result["message"] = "Test failed. A dictionary was expected as a value for the key '" + str(original_variable) + "'."
                    tested_variable_result["error"] = 1
                    continue

                # check if value is required
                if original_variable_def["required"] == False:
                    self.succeed += 1
                    tested_variable_result["message"] = "Test was successful."
                    tested_variable_result["error"] = 0
                    continue

                # check if the variable type is defined and matches
                if original_variable_def["type"] != "*":
                    if original_variable_def["type"] != tested_variable["type"]:
                        self.failed += 1
                        tested_variable_result["message"] = "Test failed. The type of the variable does not match the expected type."
                        tested_variable_result["error"] = 1
                        continue

                # check if the variable length is defined and matches
                if original_variable_def["length"] != -1:
                    if original_variable_def["length"] != tested_variable["length"]:
                        
                        self.failed += 1
                        tested_variable_result["message"] = "Test failed. The length of the variable does not match the expected length."
                        tested_variable_result["error"] = 1
                        continue

                # check if tested value is part of allowed values
                # if original list of allowed values is 0, every value is ok
                if type(original_variable_def["value"]) is list and len(original_variable_def["value"]) > 0:
                    # not necessary, it's always a list and it always contains 1 item only
                    # if type(tested_variable["value"]) is list:
                    #     test_value = tested_variable["value"][0]
                    # else:
                    #     test_value = tested_variable["value"]

                    if tested_variable["value"][0] not in original_variable_def["value"]:
                        
                        self.failed += 1
                        # TODO: add expected and actual value here
                        tested_variable_result["message"] = "Test failed. The value of the variable is not included in the list of expected values."
                        tested_variable_result["error"] = 1
                        continue

                self.succeed += 1
                tested_variable_result["message"] = "Test was successful."
                tested_variable_result["error"] = 0

        return obj_result