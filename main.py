#!/usr/bin/env python3
#
# Import invoices, expenses and contacts from iDoklad to Fakturoid
#
# Check https://api.idoklad.cz/Help/v2/ and https://www.fakturoid.cz/api

import pickle
import os
import base64

from constants import CACHE_FILE, EXPORT_DIRECTORY, EXPORT_INVOICE_DIRECTORY, EXPORT_EXPENSE_DIRECTORY
from helpers import parseargs, process_record
from idoklad_oauth2_client import IDokladOAuth2Client
from idoklad_api import IDokladAPI
from fakturoid_api import FakturoidAPI


if __name__ == "__main__":
    args = parseargs()

    idoklad_oauth_client = IDokladOAuth2Client(
        args.idoklad_client_id,
        args.idoklad_client_secret,
    )
    idoklad = IDokladAPI(idoklad_oauth_client, args.idoklad_filter)
    idoklad_invoices = idoklad.get_invoices()
    idoklad_expenses = idoklad.get_expenses()

    print("\n")

    try:
        print("--- Loading Fakturoid API cache")
        cache = pickle.load(open(CACHE_FILE, "rb"))
    except IOError:
        cache = {
            "subjects": {},
            "bank_accounts": {},
        }
    except Exception as e:
        print("WARNING: Cache load failed: {}. Continuing anyway.".format(e))
        cache = {
            "subjects": {},
            "bank_accounts": {},
        }

    cache_keys = [
        "account",
        "invoices",
        "expenses",
        "subjects",
        "bank_accounts",
    ]

    for key in cache_keys:
        if not key in cache:
            cache[key] = {}

    print("\n")

    fakturoid = FakturoidAPI(
        args.fakturoid_account_name,
        args.fakturoid_email,
        args.fakturoid_api_key,
    )
    fakturoid_account = fakturoid.get_account(cache["account"])
    fakturoid_invoices = fakturoid.get_invoices(cache["invoices"])
    fakturoid_expenses = fakturoid.get_expenses(cache["expenses"])
    fakturoid_subjects = fakturoid.get_subjects(cache["subjects"])
    fakturoid_bank_accounts = fakturoid.get_bank_accounts(
        cache["bank_accounts"],
    )

    pickle.dump(cache, open(CACHE_FILE, "wb"))

    print("\n")

    created_invoices = 0
    created_expenses = 0

    for idoklad_invoice in idoklad_invoices:
        result = process_record(
            idoklad,
            idoklad_invoice,
            fakturoid,
            fakturoid_account,
            fakturoid_subjects,
            fakturoid_bank_accounts,
            fakturoid_invoices,
            "invoice",
            args.disable_vat_number_check,
        )

        if result == 'continue':
            continue

        if result == 'break':
            break

        if args.export_idoklad_as_pdf:
            base64_idoklad_invoice = idoklad.get_invoice_pdf(
                idoklad_invoice["Id"],
            )
            file_path = "{root_dir}/{type_dir}/{name}.pdf".format(
                root_dir=EXPORT_DIRECTORY,
                type_dir=EXPORT_INVOICE_DIRECTORY,
                name=idoklad_invoice["DocumentNumber"],
            )

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as file:
                file.write(base64.b64decode(base64_idoklad_invoice))

        created_invoices += 1

        if "fakturoid_subject" in result:
            fakturoid_subjects.append(result["fakturoid_subject"])

        fakturoid_invoices.append(result["fakturoid_record"])

    for idoklad_expense in idoklad_expenses:
        result = process_record(
            idoklad,
            idoklad_expense,
            fakturoid,
            fakturoid_account,
            fakturoid_subjects,
            fakturoid_bank_accounts,
            fakturoid_expenses,
            "expense",
            args.disable_vat_number_check,
        )

        if result == 'continue':
            continue

        if result == 'break':
            break

        if args.export_idoklad_as_pdf:
            base64_idoklad_expense = idoklad.get_expense_pdf(
                idoklad_expense["Id"],
            )
            file_path = "{root_dir}/{type_dir}/{name}.pdf".format(
                root_dir=EXPORT_DIRECTORY,
                type_dir=EXPORT_EXPENSE_DIRECTORY,
                name=idoklad_expense["DocumentNumber"],
            )

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as file:
                file.write(base64.b64decode(base64_idoklad_expense))

        created_expenses += 1

        if "fakturoid_subject" in result:
            fakturoid_subjects.append(result["fakturoid_subject"])

        fakturoid_expenses.append(result["fakturoid_record"])

    print(
        "\nCreated {invoices} invoices and {expenses} expenses".format(
            invoices=created_invoices,
            expenses=created_expenses,
        )
    )
