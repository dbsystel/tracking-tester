# Copyright 2023 DB Systel GmbH
# License Apache-2.0

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
    
    def compare(self, 
                pages_before: dict = None, 
                pages_after: dict = None,
                var_mapping: dict = None) -> dict:

        """
        Compare two sets of pages before and after a change, and generate a report.

        This method takes two dictionaries representing pages before and after a change,
        and an optional variable mapping dictionary for variable name translations.

        Parameters:
        - pages_before (dict): A dictionary representing pages before the change.
        - pages_after (dict): A dictionary representing pages after the change.
        - var_mapping (dict, optional): A dictionary mapping variable names for translation.
        
        Returns:
        - result (dict): A dictionary containing the comparison report with details of the changes.

        Example:
        ```
        before = {'page1': {'var1': 10, 'var2': 20}, 'page2': {'var1': 5, 'var3': 15}}
        after = {'page1': {'var1': 12, 'var2': 20}, 'page3': {'var4': 8}}
        
        comparer = PageComparer()
        comparison_result = comparer.compare(pages_before=before, pages_after=after)
        ```
        """
            
        # loop through all pages from state "before"
        for page_before in pages_before:
            
            # check if state "after" contains current page
            if page_before not in pages_after:
                pages_before[page_before] = {
                            "message": f"Page `{page_before}`not found.",
                            "error": 1
                        }
            
            # loop through all variables from state "before"
            for var_before in pages_before[page_before]["variables"]:
                
                # if exists, get variable mapping ("readable name")
                if var_before in var_mapping:
                    pages_before[page_before]["variables"][var_before]['variable_mapping'] = var_mapping[var_before]
                    
                # check if the variable exists in state "after"
                if var_before not in pages_after[page_before]["variables"]:
                    
                    pages_before[page_before]["variables"][var_before]['message'] = f"Variable `{var_before}` was not found."
                    pages_before[page_before]["variables"][var_before]['error'] = 1

                    continue
                
                tested_variable = pages_before[page_before]["variables"][var_before]

                # if dict, then check the entries in the dictionary
                if type(tested_variable) is not dict:
                    pages_before[page_before]["variables"][var_before]["message"] = "Test failed. A dictionary was expected as a value for the key '" + str(original_variable) + "'."
                    pages_before[page_before]["variables"][var_before]["error"] = 1
                    continue

                # check if variable is mandatory/required
                if pages_before[page_before]["variables"][var_before]["required"] == False:
                    pages_before[page_before]["variables"][var_before]["message"] = "Not required."
                    pages_before[page_before]["variables"][var_before]["error"] = 0
                    continue

                # check if the variable type is defined and matches
                if pages_before[page_before]["variables"][var_before]["type"] != "*":
                    if pages_before[page_before]["variables"][var_before]["type"] != pages_after[page_before]["variables"][var_before]["type"]:
                        pages_before[page_before]["variables"][var_before]["message"] = f'The type of the variable does not match the expected type: {pages_before[page_before]["variables"][var_before]["type"]}'
                        pages_before[page_before]["variables"][var_before]["error"] = 1
                        continue

                # check if the variable length is defined and matches
                if pages_before[page_before]["variables"][var_before]["length"] > 0:
                    if pages_before[page_before]["variables"][var_before]["length"] != pages_before[page_before]["variables"][var_before]["length"]:
                        
                        pages_before[page_before]["variables"][var_before]["message"] = f'The length of the variable does not match the expected length: {pages_before[page_before]["variables"][var_before]["length"]}'
                        pages_before[page_before]["variables"][var_before]["error"] = 1
                        continue

                # check if tested value is an allowed value
                if pages_after[page_before]["variables"][var_before]["value"][0] not in pages_before[page_before]["variables"][var_before]["value"]:
                        pages_before[page_before]["variables"][var_before]["message"] = f'The value of the variable is not included in the list of expected values: {pages_before[page_before]["variables"][var_before]["value"].join(", ")}'
                        pages_before[page_before]["variables"][var_before]["error"] = 1
                        continue

                pages_before[page_before]["variables"][var_before]["error"] = 0

        return pages_before