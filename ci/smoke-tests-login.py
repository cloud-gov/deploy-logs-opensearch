#!/usr/bin/env python

import os
import logging
import requests

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    session = requests.Session()

    logs = session.get('https://dashboard-proxy.{}'.format(os.environ['CF_SYSTEM_DOMAIN']))
    print(logs.url, logs.status_code)
    assert logs.url == 'https://login.{}/login'.format(os.environ['CF_SYSTEM_DOMAIN'])
    assert logs.status_code == 200

    login = session.post(
        'https://login.{}/login.do'.format(os.environ['CF_SYSTEM_DOMAIN']),
        data={
            'username': os.environ['CF_USERNAME'],
            'password': os.environ['CF_PASSWORD'],
            'X-Uaa-Csrf': logs.cookies['X-Uaa-Csrf'],
        },
    )
    print(login.url, login.status_code)
    # proves that we're getting to the OAuth page. Need UI testing to click "Authorize" on this page
    assert login.url.startswith('https://login.{}/oauth/authorize'.format(os.environ['CF_SYSTEM_DOMAIN']))
    assert login.status_code == 200
