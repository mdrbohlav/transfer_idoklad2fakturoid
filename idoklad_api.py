import requests

from constants import ERROR_MESSAGES


class IDokladAPI(object):
    def __init__(self, oauth_client, filter):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": "Bearer {access_token}".format(
                    access_token=oauth_client.access_token
                ),
                "Accept": "application/json",
            }
        )
        self.filter = filter
        self.api_url = "https://api.idoklad.cz/v2"

    def get_records(self, path, type):
        if self.filter:
            path += "?filter={}".format(self.filter)

        page_search_param_prefix = "&" if self.filter else "?"

        total_pages = 1
        page = 1
        result = []

        print("--- iDoklad - loading {} invoices".format(type))

        while page <= total_pages:
            whole_path = "/{path}{page_search_param_prefix}page={page}&pagesize={pagesize}".format(
                page_search_param_prefix=page_search_param_prefix,
                path=path,
                page=page,
                pagesize=50
            )

            print("Loading page {}".format(page))

            response = self._api_get(whole_path)

            if response.status_code == 200:
                json_response = response.json()
                result += json_response["Data"]

                print(
                    "Loaded {so_far} of {total} invoices".format(
                        so_far=len(result),
                        total=json_response["TotalItems"]
                    )
                )

                if page == 1:
                    total_pages = json_response["TotalPages"]

                page += 1
            else:
                raise Exception(
                    ERROR_MESSAGES["request_failed"].format(
                        "GET", whole_path, response.status_code, response.text
                    ),
                )

        return result

    def get_invoices(self):
        return self.get_records("IssuedInvoices/Expand", "issued")

    def get_expenses(self):
        return self.get_records("ReceivedInvoices/Expand", "received")

    def get_pdf(self, type, id):
        if type == "invoice":
            return self.get_invoice_pdf(id)
        elif type == "expense":
            return self.get_expense_pdf(id)

        return None

    def get_invoice_pdf(self, id):
        path = "IssuedInvoices/{}/GetPdf?language=1".format(id)
        response = self._api_get("/" + path)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                ERROR_MESSAGES["request_failed"].format(
                    "GET", path, response.status_code, response.text
                ),
            )

    def get_expense_pdf(self, id):
        path = "ReceivedInvoices/{}/GetPdf?language=1".format(id)
        response = self._api_get("/" + path)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                ERROR_MESSAGES["request_failed"].format(
                    "GET", path, response.status_code, response.text
                ),
            )

    def get_attachment(self, type, id):
        if type == "invoice":
            return self.get_invoice_attachment(id)
        elif type == "expense":
            return self.get_expense_attachment(id)

        return None

    def get_invoice_attachment(self, id):
        path = "IssuedInvoices/{}/GetAttachment".format(id)
        response = self._api_get("/" + path)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                ERROR_MESSAGES["request_failed"].format(
                    "GET", path, response.status_code, response.text
                ),
            )

    def get_expense_attachment(self, id):
        path = "ReceivedInvoices/{}/GetAttachment".format(id)
        response = self._api_get("/" + path)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                ERROR_MESSAGES["request_failed"].format(
                    "GET", path, response.status_code, response.text
                ),
            )

    def _api_get(self, path):
        return self.session.get(self.api_url + path)
