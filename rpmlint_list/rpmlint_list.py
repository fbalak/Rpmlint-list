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
    pattern = re.compile("(.*):\s(.*):\s(.*)[ | ](.*)")
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
    print(error_list)
    error_dictionary = {}
    for error in error_list:
        if error[2] not in error_dictionary:
            error_type = "Error" if error[1]=="E" else\
                "Warning" if error[1]=="W" else error[1]
            error_dictionary[error[2]] = {
                "type": error_type,
                "component": {}}
        if error[3] not in error_dictionary[error[2]]["component"]:
            error_dictionary[error[2]]["component"][error[3]] = []
        error_dictionary[error[2]]["component"][error[3]].append(error[0])
    return error_dictionary


def generate_html_content(error_dictionary):
    """Generates html artefacts containing list of packages and for each
    package list of errors.

    Args:
        error_dictionary(dictionary): dictionary where key is rpm package
            and vulues are error messages.
    """
    ul = "<ul>"
    for error in error_dictionary:
        ul += "<li>{}<ul>".format(error)
        ul += "</ul><ul>".join(error_dictionary[error])
        ul += "</ul></li>"
    ul += "</ul>"
    content = """<div>
    {}
    </div>""".format(ul)
    return content
