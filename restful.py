import argparse
import urllib.parse
import json
import demjson
import re
import pprint
import os
import csv

from termcolor import colored
import requests
from requests.exceptions import RequestException

from config import API_URL, STORAGE_PATH


URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://'
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
    r'localhost|'
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    r'(?::\d+)?'
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)


class Client:

    def __init__(self, api_url=API_URL):
        self.api_url = api_url

    @staticmethod
    def get(url, data=None):
        return requests.get(url, params=data)

    @staticmethod
    def post(url, data=None):
        return requests.post(url, data=data)

    def build_url(self, uri_fragment):
        return urllib.parse.urljoin(self.api_url, uri_fragment)


class Console:

    @staticmethod
    def print_error(error_message):
        print(colored('ERROR:', 'red') + ' ' + error_message)

    @staticmethod
    def print_success(success_message):
        print(colored('SUCCESS:', 'green') + ' ' + success_message)

    @staticmethod
    def print_response(response_data):
        formatted_data = pprint.pformat(response_data, indent=4)
        print(formatted_data)


class FilesStorage:

    def __init__(self, storage_path=STORAGE_PATH):
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def save(self, filename, data):
        path = os.path.join(self.storage_path, filename)
        _, extension = os.path.splitext(filename)

        with open(path, 'w') as file:
            if extension.lower() == '.json':
                json.dump(data, file)
            else:
                csv_writer = csv.writer(file)
                for row in data:
                    csv_writer.writerow(row.values())

        return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('METHOD', help='Request method', choices=['get', 'post'])
    parser.add_argument('ENDPOINT', help='Request endpoint URI fragment', metavar='endpoint')
    parser.add_argument('-d', '--data', help='Data to send with request', metavar='DATA', type=str)
    parser.add_argument('-o', '--output', help='Output to .json or .csv file (default: dump to stdout)',
                        metavar='OUTPUT', type=str)
    args = parser.parse_args()
    parsed_args = parser.parse_args()

    try:
        client = Client()

        full_url = client.build_url(parsed_args.ENDPOINT)
        if re.match(URL_REGEX, full_url) is None:
            Console.print_error('Specified URL is not valid.')
            exit(1)

        args_data = parsed_args.data
        if args_data is not None:
            args_data = demjson.decode(args_data)

        response = getattr(client, parsed_args.METHOD)(full_url, data=args_data)
        status_code = response.status_code

        if status_code < 200 or status_code >= 300:
            Console.print_error('Http response status code: {0}.'.format(status_code))
            exit(1)
        else:
            Console.print_success('Http response status code: {0}.'.format(status_code))
            response_json = response.json()
            if parsed_args.output is None:
                Console.print_response(response_json)
            else:
                storage = FilesStorage()
                storage.save(parsed_args.output, response_json)
    except RequestException as e:
        Console.print_error('Networking exception is occurred. {0}'.format(str(e)))
    except Exception as e:
        Console.print_error('Unknown exception is occurred. {0}'.format(str(e)))
    else:
        exit(0)
    exit(1)
