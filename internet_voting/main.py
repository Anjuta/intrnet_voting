import base64
import logging
import asyncio
import argparse
import jinja2

import aiohttp_jinja2
from aiohttp_session import session_middleware, SESSION_KEY
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet
from pony.orm import db_session

from internet_voting.models import InternetVotingDB, OptionModel
from internet_voting.application import InternetVotingApplication
from internet_voting.middlewares import authorize


log = logging.getLogger('internet_voting_system')
log.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

log.addHandler(ch)

SECRET_KEY = base64.urlsafe_b64decode(fernet.Fernet.generate_key())


def create_options():
    options = ['Python', 'C++', 'C#', 'Ruby', 'C', 'JavaScript', 'Perl']

    for option in options:
        with db_session:
            OptionModel(name=option)
        log.info('Option "%r" added', option)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8080, help='Listen on this port')

    args = parser.parse_args()
    return args


async def init(loop, port):
    app = InternetVotingApplication(
        loop=loop,
        middlewares=[
            session_middleware(EncryptedCookieStorage(SECRET_KEY)),
            authorize,
        ]
    )
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('_static'))
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', port)
    return srv


def main():
    args = get_args()

    db = InternetVotingDB()
    db.init_db()
    create_options()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop, args.port))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
