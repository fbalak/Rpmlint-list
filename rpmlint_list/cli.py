# -*- coding: utf-8 -*-

"""Console script for rpmlint_list."""

import click
import rpmlint_list

@click.command()
@click.argument('url')
def main(url):
    """Creates reverse index list from provided URL with XML"""
    error_list = rpmlint_list.get_error_list(url)
    error_dictionary = rpmlint_list.get_error_dictionary(error_list)
    click.echo(error_dictionary)


if __name__ == "__main__":
    main()
