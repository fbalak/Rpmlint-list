# -*- coding: utf-8 -*-

"""Console script for rpmlint_list."""

import click
import json
import rpmlint_list


@click.command()
@click.option('--list_format', '-f', default="none",
              help='Format can be `json`, `html` or `none`. `none`\
is default.')
@click.option('--details_path', '-d',
              help='Path where will be generated web application')
@click.argument('url')
def main(list_format, details_path, url):
    """Creates reverse index list from provided URL with XML"""
    error_list = rpmlint_list.get_error_list(url)
    error_dictionary = rpmlint_list.get_error_dictionary(error_list)
    if list_format == 'html' or details_path:
        generator = rpmlint_list.HTMLGenerator(error_dictionary)
    if list_format == 'html':
        click.echo(generator.generate_html_list())
    elif list_format == 'json':
        click.echo(json.dumps(error_dictionary))
    if details_path:
        generator.generate_details(details_path)


if __name__ == "__main__":
    main()
