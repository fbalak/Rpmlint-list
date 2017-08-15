import re
from urllib.request import urlopen
import xml.etree.ElementTree as ET


def get_error_list(url):
    """Get list of tupples where first item is package where error happened
    and second item is error message.

    Args:
        url(str): URL where is located xml with report from rpmlint.
    """
    xml_content = urlopen(url)
    pattern = re.compile("(.*):\s(.:\s.*)")
    error_list = []
    e = ET.parse(xml_content).getroot()
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
        if error[1] not in error_dictionary:
            error_dictionary[error[1]] = []
        error_dictionary[error[1]].append(error[0])
    return error_dictionary


def generate_html_content(error_dictionary):
    """Generates html artefacts containing list of packages and for each
    package list of errors.

    Args:
        error_dictionary(dictionary): dictionary where key is rpm package
            and vulues are error messages.
    """
    ul = "<ul><li>"
    for error in error_dictionary:
        ul += "</li><li>".join(error_dictionary[error])
    ul += "</li></ul>"
    content = """<div>
    {}
    </div>""".format(ul)
    return content
