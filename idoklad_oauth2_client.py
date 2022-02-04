import json
from rauth import OAuth2Service

class IDokladOAuth2Client:
    def __init__(self, client_id, client_secret):
        self.access_token = None
        self.service = OAuth2Service(
            client_id=client_id,
            client_secret=client_secret,
            access_token_url="https://identity.idoklad.cz/server/connect/token",
        )

        self.get_access_token()

    def get_access_token(self):
        data = {
            "scope": "idoklad_api",
            "grant_type": "client_credentials",
        }

        session = self.service.get_auth_session(data=data, decoder=json.loads)

        self.access_token = session.access_token