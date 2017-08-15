import re
from urllib.request import urlopen
import xml.etree.ElementTree as ET


def get_error_list(url):
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
    error_dictionary = {}
    for error in error_list:
        if error[1] not in error_dictionary:
            error_dictionary[error[1]] = []
        error_dictionary[error[1]].append(error[0])
    return error_dictionary

def generate_html_content(error_json):
    ul = "<ul><li>"
    for error in error_json:
        ul += "</li><li>".join(error_json[error])
    ul +="</li></ul>"
    content = """<div>
    {}
    </div>""".format(ul)
    return content
