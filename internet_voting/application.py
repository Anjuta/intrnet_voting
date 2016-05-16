import logging
import aiohttp_jinja2
from aiohttp import web

from pony.orm import db_session, count, left_join
from aiohttp_session import get_session

from internet_voting.models import UserModel, OptionModel, VoteResultModel


log = logging.getLogger('internet_voting_system.application')


def set_session(session, user_id, request):
    session['user'] = str(user_id)
    url = request.app.router['vote_page'].url()
    raise web.HTTPFound(url)


class InternetVotingApplication(web.Application):
    async def login(self, request):
        """Аутентификация пользователя"""
        user_data = await request.json()
        log.debug(
            'Попытка залогиниться с данными: login=%r, password=%r', user_data['login'], user_data['password']
        )

        with db_session:
            user = UserModel.get(login=user_data['login'], password=user_data['password'])
            if user:
                user = user.to_dict()

        if not user:
            raise RuntimeError(
                'Пользователя с login=%r, password=%r не существует', user_data['login'], user_data['password']
            )

        session = await get_session(request)
        set_session(session, user['id'], request)

    async def create_user(self, request):
        """Добавление нового пользователя"""
        user = await request.json()

        user = UserModel.from_dict(user)
        session = await get_session(request)
        set_session(session, user['id'], request)

    async def get_options(self, request):
        """Получить все варианты для голосования в виде списка диктов"""
        with db_session:
            users = [option.to_dict() for option in OptionModel.select()]

        return web.json_response(users)

    async def get_results(self, request):
        """Получение результатов голосования (список диктов)"""
        with db_session:
            result = left_join(
                (o.name, count(r))
                for o in OptionModel
                for r in o.vote
            )[:]

        return web.json_response(result)

    async def vote(self, request):
        """Добавление записи голосования пользователя"""
        vote = await request.json()
        VoteResultModel.add_vote(vote)

        return web.Response()

    @aiohttp_jinja2.template('voting.html')
    async def show_vote_page(self, request):
        with db_session:
            options = [o.to_dict() for o in OptionModel.select()]

        return {
            'options': options,
        }

    async def signout(self, request):
        """Разлогиниться"""
        session = get_session()
        session['user'] = None

    def make_handler(self, **kwargs):
        self.router.add_route('GET', '/options', self.get_options)
        self.router.add_route('POST', '/signin', self.create_user)
        self.router.add_route('GET', '/result', self.get_results)
        self.router.add_route('GET', '/vote', self.show_vote_page)
        self.router.add_route('POST', '/vote', self.vote, name='vote_page')
        self.router.add_route('POST', '/login', self.login)
        self.router.add_route('POST', '/signout', self.signout)
        self.router.add_static(prefix='/login', path='_static', name='login_page')
        self.router.add_static(prefix='/_static', path='_static')

        return super().make_handler(**kwargs)
