import re
import os
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
            pattern2.sub(
                "-", pattern1.sub("-", x)) for x in error_list[error_idx]]

    return error_list


def get_error_dictionary(error_list, priority_info=None):
    """Creates dictionary where key is rpm package and values are error
    messages.

    Args:
        error_list(list): List of tupples where first where first item is
            package where error happened and second item is
            error message.
        priority_info(dict): Dictionary with containing error name as a key
            and its priority as value.
    """
    error_dictionary = {}
    for error in error_list:
        error_type = "Error" if error[1] == "E" else\
            "Warning" if error[1] == "W" else error[1]
        if error_type not in error_dictionary:
            error_dictionary[error_type] = {}
        if error[2] not in error_dictionary[error_type]:
            error_dictionary[error_type][error[2]] = {}
            error_dictionary[error_type][error[2]]["detail"] = {}
            if priority_info:
                if error[2] in priority_info:
                    error_dictionary[error_type][error[2]]["priority"] =\
                        priority_info[error[2]]
                else:
                    error_dictionary[error_type][error[2]]["priority"] = 0
            else:
                error_dictionary[error_type][error[2]]["priority"] = None
        if error[3] not in error_dictionary[error_type][error[2]]["detail"]:
            error_dictionary[error_type][error[2]]["detail"][error[3]] = []
        error_dictionary[error_type][error[2]]["detail"][error[3]].append(
            error[0])
    return error_dictionary


def load_priority_info(path):
    """Loads a dictionary containing error name as a key and its priority
    as its value from configuration file on given path.

    Args:
        path(str): Path to configuration file.
    """
    with open(path) as priority_file:
        content = priority_file.readlines()
    configuration = dict(x.strip().split(None, 1) for x in content)
    return configuration


class HTMLGenerator:
    """Handle html output for provided dictionary/list."""

    def __init__(self, error_dictionary):
        self.error_dictionary = error_dictionary
        self.output = ""

    def nice_error_format(self, detail_dictionary):
        """Get Html 2 level list with error details and relevant packages.

        Args:
            detail_dictionary(dict): key is error and values are packages.
        """
        output = ""
        for detail in detail_dictionary.keys():
            output += "<h4>{}</h4><ul><li>".format(detail)
            output += "</li><li>".join(detail_dictionary[detail])
            output += "</li></ul>"
        return output

    def convert_dictionary_to_list(self, obj, indent=0, error_type="Warning"):
        """Creates recursively html list structure from dictionary/list.

        Args:
            obj: dictionary, list or string that is turned into a html.
        """
        if obj:
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

    def get_html_header(self, position=""):
        """Generate string containing html header.

        Args:
            position(str): relative or absolute position of sources."""
        return """<html>
    <head><title>Rpmlint list</title>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"initial-scale=1.0;
maximum-scale=1.0; width=device-width;\">
<link rel=\"stylesheet\" href=\"{}sources/style.css\">
<script src=\"{}sources/sorttable.js\"></script>
<style>th{{background-color:#e0e0e0;color:#000;}}
table{{margin: 50 50 50 50}}
h1{{margin-left: 50}}</style>
    </head>
    <body>""".format(position, position)

    def get_html_footer(self, scripts=None):
        """Geenrate string containing html footer.

        Args:
            scripts(str): String that is put before </body> tag.
        """
        if scripts:
            return """{}
    </body>
</html>""".format(scripts)
        else:
            return "</body></html>"

    def download_sources(self, directory):
        """Download and save css and js files into directory.

        Args:
            directory(str): path to directory with sources.
        """
        directory = os.path.join(directory, "sources")
        if not os.path.exists(directory):
            os.makedirs(directory)
        request_js = requests.get(
            "https://kryogenix.org/code/browser/sorttable/sorttable.js")
        with open(os.path.join(directory, "sorttable.js"), "w+") as file_js:
                file_js.write(request_js.text)

        request_css = requests.get(
            "https://unpkg.com/purecss@1.0.0/build/pure-min.css")
        with open(os.path.join(directory, "style.css"), "w+") as file_css:
                file_css.write(request_css.text)

    def generate_html_list(self):
        """Generates html artefacts containing list of packages and for each
        package list of errors.

        Args:
            error_dictionary(dictionary): dictionary where key is rpm package
                and vulues are error messages.
        """
        self.output = ""
        self.convert_dictionary_to_list(self.error_dictionary)
        scripts = """<script type='text/javascript' \
src="js/CollapsibleLists.js"></script>
<script>CollapsibleLists.apply()</script>"""
        content = """{}
        <ul class="collapsibleList">
        {}
        </ul>
{}""".format(
            self.get_html_header(), self.output, self.get_html_footer(scripts))
        return content

    def convert_dictionary_to_table(self, error_dictionary, error_type, error):
        """Generate html table with two columns.

        Args:
            error_dictionary(dictionary): dictionary where key is rpm package
                and values are error messages.
        """
        packages = {}
        errors = []
        for detail in error_dictionary["detail"].keys():
            error_detail = "{} {}".format(error, detail)
            errors.append(error_detail)
            packages[error_detail] = error_dictionary["detail"][detail]
        if error_type == "Error":
            url = "https://fedoraproject.org/wiki/ParagNemade/\
CommonRpmlintErrors#{}".format(error)
        else:
            url = None
        cells = "<tr><th>Name:</th><td>{}</td></tr>".format(error)
        cells += "<tr><th>Severity:</th><td>{}</td></tr>".format(error_type)
        cells += "<tr><th>Details:</th><td>{}</td></tr>".format(
            self.nice_error_format(packages))
        if url:
            cells += """<tr><th>URL:</th><td><a href=\"{}\">{}</a></td>
                </tr>""".format(url, url)
        if error_dictionary["priority"]:
            cells += "<tr><th>Priority:</th><td>{}</td></tr>".format(
                error_dictionary["priority"])

        table = "<table class=\"pure-table pure-table-horizontal\">{}</table>"\
                .format(cells)
        return table

    def generate_detail(self, error_dictionary, error_type, error):
        """Generates html artefacts containing table with error or warning
        details.

        Args:
            error_dictionary(dictionary): dictionary where key is rpm package
                and values are error messages.
        """
        table = self.convert_dictionary_to_table(
            error_dictionary,
            error_type,
            error)
        # self.convert_dictionary(self.error_dictionary)
        content = """{}
        {}
{}""".format(self.get_html_header("../"), table, self.get_html_footer())
        return content

    def generate_error_list(self, error_dictionary):
        """Generate sortable table with errors and their statisctics.

        Args:
            error_dictionary(dict): dictionary object with information
                about errors and warnings.
        """
        output = ""
        for error_severity in error_dictionary.keys():
            output += "<h1>{}</h1>".format(error_severity)
            output += "<table class=\"sortable pure-table\"><thead><tr>"
            output += "<th>Name</th><th>Number of packages</th>"
            output += "<th>Priority</th><th>Details</th></thead><tbody>"
            for error in error_dictionary[error_severity].keys():
                output += "<tr><td>{}</td>".format(error)
                pkg_count = 0
                for detail in\
                        error_dictionary[error_severity][error]["detail"]:
                    pkg_count += len(error_dictionary[error_severity]
                                     [error]["detail"][detail])
                output += "<td>{}</td>".format(pkg_count)
                output += "<td>{}</td>".format(
                    error_dictionary[error_severity][error]["priority"])
                output += "<td><a href='{}/{}.html'>link</a></td>".format(
                    error_severity.lower(), error)
                output += "</tr>"
            output += "</tbody></table>"
        return output

    def generate_details(self, error_dictionary, path):
        """Generate html page for each error in error_dictionary on given path.

        Args:
            error_dictionary(dict): dictionary object with information
                about errors and warnings.
        """
        if not os.path.exists(path):
            raise OSError(2, 'No such file or directory', path)

        tables = self.generate_error_list(error_dictionary)
        self.download_sources(path)

        with open(os.path.join(path, "index.html"), "w+") as file_o:
            file_o.write("{}{}{}".format(
                self.get_html_header(), tables, self.get_html_footer()))

        for error_type in error_dictionary.keys():
            for error in error_dictionary[error_type].keys():
                content = self.generate_detail(
                    error_dictionary[error_type][error], error_type, error)

                directory = os.path.join(path, error_type.lower())
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(
                    os.path.join(
                        directory, "{}.html".format(error)), "w+") as file_o:
                    file_o.write(content)
