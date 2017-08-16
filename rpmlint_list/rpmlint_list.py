import re
import requests
import xml.etree.ElementTree as ET


def get_error_list(url):
    """Get list of tupples where first item is package where error happened
    and second item is error message.

    Args:
        url(str): URL where is located xml with report from rpmlint.
    """
    xml_content = requests.get(url)
    pattern = re.compile("(.*):\s(.*):\s(.*)[ | | ](.*)")
    error_list = []
    e = ET.fromstring(xml_content.text)
    for test_case in e.findall("testcase"):
        failure = test_case.find('failure')
        if failure is not None:
            error_list += pattern.findall(failure.text)
    return error_list


def get_error_dictionary(error_list):
    """Creates dictionary where key is rpm package and vulues are error messages.

    Args:
        error_list(list): List of tupples where first where first item is
            package where error happened and second item is
            error message.
    """
    error_dictionary = {}
    for error in error_list:
        if error[2] not in error_dictionary:
            error_type = "Error" if error[1] == "E" else\
                "Warning" if error[1] == "W" else error[1]
            error_dictionary[error[2]] = {
                "type": error_type,
                "component": {}}
        if error[3] not in error_dictionary[error[2]]["component"]:
            error_dictionary[error[2]]["component"][error[3]] = []
        error_dictionary[error[2]]["component"][error[3]].append(error[0])
    return error_dictionary


class HTMLGenerator:
    """Handle html output for provided dictionary/list."""

    def __init__(self, error_dictionary):
        self.error_dictionary = error_dictionary
        self.output = ""

    def convert_dictionary(self, obj, indent=0):
        """Creates recursively html list structure from dictionary/list.

        Args:
            obj: dictionary, list or string that is turned into a html.
        """
        if len(obj):
            self.output += '\n{}<ul>'.format('  ' * indent)
            if type(obj) is dict:
                for k, v in obj.items():
                    self.output += '\n{}<li>{}</li>'.format(
                                    '  ' * (indent+1), k)
                    self.convert_dictionary(v, indent+1)
            elif type(obj) is list:
                for k, v in enumerate(obj):
                    self.convert_dictionary(v, indent+1)
            elif type(obj) is str:
                self.output += '\n{}<li>{}</li>'.format(
                                    '  ' * (indent+1), obj)
            self.output += '\n{}</ul>'.format('  ' * indent)

    def generate(self):
        """Generates html artefacts containing list of packages and for each
        package list of errors.

        Args:
            error_dictionary(dictionary): dictionary where key is rpm package
                and vulues are error messages.
        """
        self.convert_dictionary(self.error_dictionary)
        content = """<div>
        {}
        </div>""".format(self.output)
        return content
