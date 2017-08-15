# -*- coding: utf-8 -*-

"""Console script for rpmlint_list."""

import click
import json
import rpmlint_list


@click.command()
@click.option('--html', '-h', is_flag=True,
              help='Generates html output for provided XML.')
@click.argument('url')
def main(html, url):
    """Creates reverse index list from provided URL with XML"""
    error_list = rpmlint_list.get_error_list(url)
    error_dictionary = rpmlint_list.get_error_dictionary(error_list)
    if html:
        click.echo(rpmlint_list.generate_html_content(error_dictionary))
    else:
        click.echo(json.dumps(error_dictionary))


if __name__ == "__main__":
    main()
