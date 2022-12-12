import json

from database import Database


class Filters:
    def __init__(self, db: Database):
        self.db = db

    def notRegisteredMessage(self):
        return lambda message: not(self.db.user_registered(user_id=message.chat.id))

    def notRegisteredQuery(self):
        return lambda query: not(self.db.user_registered(user_id=query.message.chat.id))

    def RegisteredMessage(self):
        return lambda message: self.db.user_registered(user_id=message.chat.id)

    def RegisteredQuery(self):
        return lambda query: self.db.user_registered(user_id=query.message.chat.id)

    def isPublicMessage(self):
        return lambda message: message.chat.type != 'private'

    def isPublicQuery(self):
        return lambda query: query.message.chat.type != 'private'

    def Query(self, query_string: str):
        return lambda query: json.loads(query.data)['action'] == query_string
