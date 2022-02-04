import requests

from constants import ERROR_MESSAGES


class FakturoidAPI(object):
    def __init__(self, account_name, email, api_key):
        self.session = requests.Session()
        self.session.auth = (email, api_key)
        self.session.headers.update(
            {
                "User-Agent": "transfer_idoklad2fakturoid (m.drbohlav1@gmail.com)"
            }
        )

        self.api_url = "https://app.fakturoid.cz/api/v2/accounts/{slug}".format(
            slug=account_name,
        )

    def get_records(self, cache, cache_headers, type, path):
        headers = {}
        total_pages = 1
        page = 1
        result = []

        if not type in cache:
            cache[type] = {}

        print("--- Fakturoid - loading {}".format(type))

        while page <= total_pages:
            print("Loading page {}".format(page))

            if page in cache[type]:
                if "headers" in cache[type][page]:
                    headers = cache[type][page]["headers"]
                else:
                    cache[type][page]["headers"] = {}
            else:
                cache[type][page] = {"headers": {}}

            whole_path = "/{path}?page={page}".format(path=path, page=page)
            response = self._api_get(path=whole_path, headers=headers)

            for header_key in cache_headers:
                if header_key in response.headers:
                    cache[type][page]["headers"][cache_headers[header_key]
                                                 ] = response.headers[header_key]

            if "last" in response.links:
                total_pages = response.links["last"]

            if response.status_code == 200 or response.status_code == 304:
                data = []

                if response.status_code == 200:
                    data = response.json()
                    cache[type][page]["data"] = data
                elif "data" in cache[type][page]:
                    print("Cache hit for page {}".format(page))

                    data = cache[type][page]["data"]
                else:
                    print("Cache miss, reload page {}".format(page))

                    headers["If-None-Match"] = "W/\"reload\""

                    continue

                result += data

                print(
                    "Loaded page {page} of {total_pages}, so far {so_far} {type}".format(
                        page=page,
                        total_pages=total_pages,
                        so_far=len(result),
                        type=type,
                    )
                )

                page += 1
            else:
                raise Exception(
                    ERROR_MESSAGES["request_failed"].format(
                        "GET", whole_path, response.status_code, response.text
                    ),
                )

        return result

    def get_invoices(self, cache):
        return self.get_records(cache, {"ETag": "If-None-Match"}, "invoices", "invoices.json")

    def get_expenses(self, cache):
        return self.get_records(cache, {"ETag": "If-None-Match"}, "expenses", "expenses.json")

    def get_subjects(self, cache):
        return self.get_records(cache, {"ETag": "If-None-Match"}, "subjects", "subjects.json")

    def get_bank_accounts(self, cache):
        return self.get_records(
            cache,
            {"ETag": "If-None-Match"},
            "bank_accounts",
            "bank_accounts.json",
        )

    def create_subject(self, subject):
        path = "subjects.json"
        response = self._api_post("/" + path, subject)

        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(
                ERROR_MESSAGES["request_failed"].format(
                    "POST", path, response.status_code, response.text
                ),
            )

    def create_record(self, path, item):
        response = self._api_post("/" + path, item)

        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(
                ERROR_MESSAGES["request_failed"].format(
                    "POST", path, response.status_code, response.text
                ),
            )

    def create_invoice(self, invoice):
        return self.create_record("invoices.json", invoice)

    def create_expense(self, expense):
        return self.create_record("expenses.json", expense)

    def pay_record(self, type, id, payload):
        if type == "invoice":
            self.pay_invoice(id, payload)
        elif type == "expense":
            self.pay_expense(id, payload)

    def pay_invoice(self, id, payload):
        path = "invoices/{}/fire.json?event=pay".format(id)
        response = self._api_post("/" + path, payload)

        if not response.status_code == 200:
            raise Exception(
                ERROR_MESSAGES["request_failed"].format(
                    "POST", path, response.status_code, response.text
                ),
            )

    def pay_expense(self, id, payload):
        path = "expenses/{}/fire.json?event=pay".format(id)
        response = self._api_post("/" + path, payload)

        if not response.status_code == 200:
            raise Exception(
                ERROR_MESSAGES["request_failed"].format(
                    "POST", path, response.status_code, response.text
                ),
            )

    def _api_get(self, path, headers={}):
        return self.session.get(self.api_url + path, headers=headers)

    def _api_post(self, path, payload):
        return self.session.post(self.api_url + path, json=payload)
