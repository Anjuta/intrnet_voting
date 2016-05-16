import logging

from pony.orm import Database, Required, db_session, flush, Optional


log = logging.getLogger('internet_voting_system.models')
db = Database()


class UserModel(db.Entity):
    __table__ = 'users'

    login = Required(str, unique=True, nullable=False)
    password = Required(str, nullable=False)
    email = Required(str, unique=True, nullable=False)
    vote_result=Optional('VoteResultModel')

    def to_dict(self):
        return {
            'id': self.id,
            'login': self.login,
            'password': self.password,
        }

    @classmethod
    def from_dict(self, user):
        with db_session:
            user = UserModel(
                login=user['login'],
                password=user['password'],
                email=user['email'],
            )
            flush()  # Чтобы сразу получить id
            user = user.to_dict()

        log.info('New user added: login=%r, password=%r', user['login'], user['password'])
        return user


class VoteResultModel(db.Entity):
    __table__ = 'vote_results'

    voting = Required('UserModel', unique=True)
    option = Required('OptionModel', nullable=False)

    @classmethod
    def add_vote(cls, vote):
        with db_session:
            VoteResultModel(voting=vote['user'], option=vote['option'])


class OptionModel(db.Entity):
    __table__ = 'options'

    name = Required(str, unique=True, nullable=False)
    vote = Optional('VoteResultModel')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class InternetVotingDB(object):
    def init_db(self):
        db.bind('sqlite', ':memory:', create_db=True)
        db.generate_mapping(create_tables=True)
