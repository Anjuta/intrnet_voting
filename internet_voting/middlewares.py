import logging

from aiohttp import web
from aiohttp_session import get_session, setup


log = logging.getLogger('internet_voting_system.middlewares')


async def authorize(app, handler):
    async def middleware(request):
        def check_path(path):
            result = True
            for r in ['/login', '/_static/', '/signin', '/_debugtoolbar/']:
                if path.startswith(r):
                    result = False
            return result

        session = await get_session(request)
        if session.get("user"):
            if request.path.startswith('/login'):
                url = request.app.router['vote_page'].url()
                raise web.HTTPFound(url)
            return await handler(request)
        elif check_path(request.path):
            url = request.app.router['login_page'].url(filename='login.html')
            raise web.HTTPFound(url)
        else:
            return await handler(request)

    return middleware
