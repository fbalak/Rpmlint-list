import re
import os
import errno
import requests
import xml.etree.ElementTree as ET


def get_error_list(url):
    """Get list of tupples where first item is package where error happened
    and second item is error message.

    Args:
        url(str): URL where is located xml with report from rpmlint.
    """
    xml_content = requests.get(url)
    pattern = re.compile("(.*):\s(.):\s([^\s]+)\s(.*)")
    error_list = []
    e = ET.fromstring(xml_content.text)
    for test_case in e.findall("testcase"):
        failure = test_case.find('failure')
        if failure is not None:
            error_list += pattern.findall(failure.text)
    pattern1 = re.compile("^-+$")
    pattern2 = re.compile("^$")
    for error_idx in range(len(error_list)):
        error_list[error_idx] = [
            pattern2.sub("-", pattern1.sub("-", x)) for
                x in error_list[error_idx]]

    return error_list


def get_error_dictionary(error_list):
    """Creates dictionary where key is rpm package and values are error messages.

    Args:
        error_list(list): List of tupples where first where first item is
            package where error happened and second item is
            error message.
    """
    error_dictionary = {}
    for error in error_list:
        error_type = "Error" if error[1] == "E" else\
            "Warning" if error[1] == "W" else error[1]
        if error_type not in error_dictionary:
            error_dictionary[error_type] = {}
        if error[2] not in error_dictionary[error_type]:
            error_dictionary[error_type][error[2]] = {}
        if error[3] not in error_dictionary[error_type][error[2]]:
            error_dictionary[error_type][error[2]][error[3]] = []
        error_dictionary[error_type][error[2]][error[3]].append(error[0])
    return error_dictionary


class HTMLGenerator:
    """Handle html output for provided dictionary/list."""

    def __init__(self, error_dictionary):
        self.error_dictionary = error_dictionary
        self.output = ""

    def convert_dictionary_to_list(self, obj, indent=0, error_type="Warning"):
        """Creates recursively html list structure from dictionary/list.

        Args:
            obj: dictionary, list or string that is turned into a html.
        """
        if len(obj):
            if type(obj) is dict:
                for k, v in obj.items():
                    if indent == 0:
                        error_type = k
                    self.output +=\
                        '\n{}<li><a class="item" href="#">{}</a>'.format(
                                    '  ' * (indent+1), k)

                    # Add link to error description
                    if indent == 2 and error_type == "Error":
                        self.output += (
                                        " <a href='http://wiki.rosalab.ru/en/"
                                        "index.php/Rpmlint_Errors#{}' target="
                                        "'_blank'>details</a>".format(k))
                    self.output += '\n{}<ul>'.format('  ' * (indent+1))
                    self.convert_dictionary_to_list(v, indent+2, error_type)
                    self.output += '\n{}</ul>'.format('  ' * (indent+1))
                    self.output += '\n{}</li>'.format(
                        '  ' * (indent+1))
            elif type(obj) is list:
                for k, v in enumerate(obj):
                    self.convert_dictionary_to_list(v, indent+1, error_type)
            elif type(obj) is str:
                self.output += '\n{}<li>{}</li>'.format(
                                    '  ' * (indent+1), obj)

    def get_html_header(self):
        return """<html>
    <head><title>Rpmlint list</title>
    <style>
    .item {
      color: inherit;
      text-decoration: inherit;
    }
    </style>
    </head>
    <body>"""

    def get_html_footer(self):
        return """    <script type='text/javascript' \
src="js/CollapsibleLists.js"></script>
    <script>CollapsibleLists.apply()</script>
    </body>
</html>"""

    def generate_html_list(self):
        """Generates html artefacts containing list of packages and for each
        package list of errors.

        Args:
            error_dictionary(dictionary): dictionary where key is rpm package
                and vulues are error messages.
        """
        self.output = ""
        self.convert_dictionary_to_list(self.error_dictionary)
        content = """{}
        <ul class="collapsibleList">
        {}
        </ul>
{}""".format(self.get_html_header(), self.output, self.get_html_footer())
        return content


    def convert_dictionary_to_table(self, error_dictionary, error_type, error):
        """Generate html table with two columns.

        Args:
            error_dictionary(dictionary): dictionary where key is rpm package
                and values are error messages.
        """
        packages = {}
        errors = []
        for detail in error_dictionary.keys():
            error_detail = "{} {}".format(error, detail)
            errors.append(error_detail)
            packages[error_detail] = detail
        if error_type == "Error":
            url = "http://wiki.rosalab.ru/en/index.php/Rpmlint_Errors#{}".format(
                error)
        else:
            url = None
        cells = "<tr><td>Name:</td><td>{}</td></tr>".format(error)
        cells += "<tr><td>Severity:</td><td>{}</td></tr>".format(error_type)
        cells += "<tr><td>Details:</td><td>{}</td></tr>".format(errors)
        if url:
            cells += "<tr><td>URL:</td><td>{}</td></tr>".format(url)

        table = "<table>{}</table>".format(cells)
        return table


    def generate_detail(self, error_dictionary, error_type, error):
        """Generates html artefacts containing table with error or warning
        details.

        Args:
            error_dictionary(dictionary): dictionary where key is rpm package
                and values are error messages.
        """
        table = self.convert_dictionary_to_table(error_dictionary, error_type, error)
        # self.convert_dictionary(self.error_dictionary)
        content = """{}
        {}
{}""".format(self.get_html_header(), table, self.get_html_footer())
        return content

    def generate_details(self, error_dictionary, path):
        """Generate html page for each error in error_dictionary on given path.

        Args:
            error_dictionary(dictionary): dictionary object with information
                about errors and warnings.
        """
        if not os.path.exists(path):
            raise OSError(2, 'No such file or directory', path)
            exit(1)
        for error_type in error_dictionary.keys():
            for error in error_dictionary[error_type].keys():
                content = self.generate_detail(error_dictionary[error_type][error], error_type, error)

                directory = os.path.join(path, error_type)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(os.path.join(directory, "{}.html".format(error)), "w+") as f:
                    f.write(content)
