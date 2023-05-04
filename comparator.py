# Copyright 2023 DB Systel GmbH
# License Apache-2.0

from email import message
import json
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

class Comparator():
    
    keyword = "variables"
    obj_original: dict = {}
    
    defined: bool = False

    succeed: int = 0
    failed: int = 0

    # The initialization of the class requires a dictionary.
    def __init__(self, obj_original: dict) -> None:

        self.define_original(obj_original)

    # The method passes the dictionary and checks if it 
    # contains the required variables and the correct format.
    def define_original(self, obj_original: dict) -> None:

        if self.check_json_format(obj_original) == True:

            self.obj_original = obj_original
            self.defined = True

        else:

            self.obj_original = None
            self.defined = False
            raise error("The JSON object could not be read in because the format is not passed as expected.")

    # Returns a value of type boolean if the comparator object
    # is initialized
    def is_defined(self) -> bool:
        return self.defined

    # Returns the number of tested pages from the last test 
    # run (call of the function check_json()).
    def get_tested(self) -> int:
        return (self.succeed + self.failed)

    # Returns the number of successfully tested pages from 
    # the last test run (call to check_json() function).
    def get_succeed(self) -> int:
        return self.succeed
    
    # Returns the number of failed tested pages from the last 
    # test run (call to check_json() function).
    def get_failed(self) -> int:
        return self.failed

    # Static method which returns the type of an passed object.
    @staticmethod
    def check_type(obj) -> type:
        return type(obj)

    # Static method which passes a value of type boolean if 
    # the object was defined correct.
    @staticmethod
    def check_defined(obj) -> bool:
        if type(obj) is str and len(obj) > 0:
            return True
        
        if (type(obj) is int or type(obj) is float) and obj != -1:
            return True
        
        return False

    # The method checks that the given format of the JSON file 
    # is correct and returns a boolean.
    @staticmethod
    def check_json_format(json: any, orginial: bool = False):

        pages = json

        if type(pages) is not dict:
            raise error("[FormatCheck] JSON is not defined as dictionary. " + str(type(pages)))
        
        if len(pages) <= 0:
            raise error("[FormatCheck] No elements available in the JSON. " + str(len(pages)))

        for page in pages:
            if type(pages[page]) is not dict:
                    raise error("[FormatCheck] Page '" + str(page) + "' is not defined as dictionary. " + str(type(pages[page])))
    

            if "variables" not in pages[page]:
                raise error("[FormatCheck] There are no variable definitions for the page '" + str(page) + "'.")

            
            variables = pages[page][Comparator.keyword]
            for variable in variables:

                if type(pages[page][Comparator.keyword][variable]) is not dict:
                    raise error("[FormatCheck] Variable '" + str(variable) + "' in page '" + str(page) + "' is not defined as dictionary. " + str(type(pages[page][variable])))
    

                if "value" not in pages[page][Comparator.keyword][variable]:
                    raise error("[FormatCheck] Value in variable '" + str(variable) + "' in page '" + str(page) + "' is not defined.")
    
                _value = pages[page][Comparator.keyword][variable]["value"]
                if type(_value) is not list:
                    raise error("[FormatCheck] The type of value in variable '" + str(variable) + "' in page '" + str(page) + "' is not a list.")

                if "type" not in pages[page][Comparator.keyword][variable]:
                    raise error("[FormatCheck] Type in variable '" + str(variable) + "' in page '" + str(page) + "' is not defined.")
    

                _type = pages[page][Comparator.keyword][variable]["type"]
                if _type != "int" and _type != "float" and _type != "str" and _type != "*":
                    raise error("[FormatCheck] Value for type in variable '" + str(variable) + "' in page '" + str(page) + "' is not invalid. " + str(_type))
    

                if "length" not in pages[page]["variables"][variable]:
                    raise error("[FormatCheck] Length in variable '" + str(variable) + "' in page '" + str(page) + "' is not defined.")
    

                if "required" not in pages[page]["variables"][variable]:
                    raise error("[FormatCheck] Required in variable '" + str(variable) + "' in page '" + str(page) + "' is not defined.")
    

                _required = pages[page]["variables"][variable]["required"]
                if _required is not True and _required is not False:
                    raise error("[FormatCheck] Value for required in variable '" + str(variable) + "' in page '" + str(page) + "' is not invalid. " + str(_required))
    

        return True

    # Checks the passed JSON object for the correct format and 
    # then if the passed values match what is expected from 
    # the original JSON.
    def check_json(self, obj_test, obj_mapping) -> dict:
        
        if self.check_json_format(obj_test) != True:
            raise error("The test was not processed because the format of the test JSON is not passed as expected.")

        obj_result = obj_test.copy()

        self.succeed = 0
        self.failed = 0

        # loop through the pages
        for original_page in self.obj_original:
            
            if original_page not in obj_test:
                raise error("Execution stopped! Page '" + str(original_page) + "' was not found in the JSON object.")
                # or use continue for ignore the missing pages

            original_variables = self.obj_original[original_page][self.keyword]
            # loop through the adobe analytics variables
            for original_variable in original_variables:
                
                original_variable_def = original_variables[original_variable]

                # check if the variable exists in the JSON
                if original_variable not in obj_test[original_page][self.keyword]:
                    
                    self.failed += 1

                    obj_result[original_page][self.keyword][original_variable] = {
                        "value": [""],
                        "message": "Test failed. Variable was not found in the list of variables.",
                        "error": 1
                    }

                    if original_variable in obj_mapping:
                        obj_result[original_page][self.keyword][original_variable]['variable_mapping'] = obj_mapping[original_variable]
                    else:
                        obj_result[original_page][self.keyword][original_variable]['variable_mapping'] = '-'

                    continue

                tested_variable_result = obj_result[original_page][self.keyword][original_variable]

                if original_variable in obj_mapping:
                    tested_variable_result['variable_mapping'] = obj_mapping[original_variable]
                else:
                    tested_variable_result['variable_mapping'] = '-'
                
                tested_variable = obj_test[original_page][self.keyword][original_variable]

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





if __name__ == '__main__':
    
    with open("test.json") as jfile:
        original = json.load(jfile)

    with open("test_copy.json") as jfile:
        test = json.load(jfile)

    comparator = Comparator(original)
    result = comparator.check_json(test)

    print("##################### Comparator #####################")
    print("\tTested: " + str(comparator.get_tested()) + " | Succeed: " + str(comparator.get_succeed()) + " | Failed: " + str(comparator.get_failed()) + "\n")
    print("######################################################")
    
    print(str(result) + "\n")
