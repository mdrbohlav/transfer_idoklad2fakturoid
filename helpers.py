import sys
import argparse

from constants import PAYMENT_METHOD_IDOKLAD_TO_FAKTUROID, ERROR_MESSAGES


def parseargs():
    parser = argparse.ArgumentParser(
        description="Import invoices from iDoklad to Fakturoid",
        add_help=False)
    parser.add_argument("--fakturoid-account",
                        type=str,
                        metavar="NAME",
                        dest="fakturoid_account_name",
                        required=True,
                        help="Fakturoid account name")
    parser.add_argument("--fakturoid-email",
                        type=str,
                        metavar="EMAIL",
                        dest="fakturoid_email",
                        required=True,
                        help="Fakturoid email address")
    parser.add_argument("--fakturoid-api-key",
                        type=str,
                        metavar="API_KEY",
                        dest="fakturoid_api_key",
                        required=True,
                        help="Fakturoid API key")
    parser.add_argument("--idoklad-client-id",
                        type=str,
                        metavar="CLIENT_ID",
                        dest="idoklad_client_id",
                        required=True,
                        help="iDoklad client ID")
    parser.add_argument("--idoklad-client-secret",
                        type=str,
                        metavar="CLIENT_SECRET",
                        dest="idoklad_client_secret",
                        required=True,
                        help="iDoklad client secret")
    parser.add_argument("--idoklad-filter",
                        type=str,
                        metavar="FILTER",
                        dest="idoklad_filter",
                        help="iDoklad filter")
    return parser.parse_args(sys.argv[1:])


def make_subject(idoklad_subject, type):
    return {
        "type": type,
        "name": idoklad_subject["CompanyName"],
        "street": idoklad_subject["Street"],
        "city":	idoklad_subject["City"],
        "zip": idoklad_subject["PostalCode"],
        "country": idoklad_subject["Country"]["Code"],
        "registration_no": idoklad_subject["IdentificationNumber"],
        "vat_no": idoklad_subject["VatIdentificationNumber"],
        "local_vat_no": idoklad_subject["VatIdentificationNumberSk"],
        "enabled_reminders": False,
        "full_name": " ".join([
            idoklad_subject["Firstname"],
            idoklad_subject["Surname"],
        ]).strip(),
        "email": idoklad_subject["Email"],
        "phone": idoklad_subject["Mobile"],
        "web": idoklad_subject["Www"],
    }


def make_attachment(base64):
    return "data:application/pdf;base64," + base64


def find_fakturoid_payment_method(idoklad_record):
    if idoklad_record["PaymentOption"]["Code"] in PAYMENT_METHOD_IDOKLAD_TO_FAKTUROID:
        return PAYMENT_METHOD_IDOKLAD_TO_FAKTUROID[idoklad_record["PaymentOption"]["Code"]]
    else:
        raise Exception(
            ERROR_MESSAGES["unknown_payment_method"].format(
                idoklad_record["PaymentOption"]["Code"],
                idoklad_record["DocumentNumber"],
            )
        )


def find_fakturoid_subject_id(fakturoid_subjects, idoklad_purchaser):
    for subject in fakturoid_subjects:
        if subject["registration_no"] == idoklad_purchaser["IdentificationNumber"]:
            return subject["id"]

    return False


def find_fakturoid_bank_account_id(fakturoid_bank_accounts, idoklad_record):
    idoklad_bank_account = "/".join([
        idoklad_record["MyCompanyDocumentAddress"]["AccountNumber"],
        idoklad_record["MyCompanyDocumentAddress"]["BankNumberCode"]
    ])

    for bank_account in fakturoid_bank_accounts:
        if bank_account["number"] == idoklad_bank_account:
            return bank_account["id"]

    raise Exception(
        ERROR_MESSAGES['bank_account_not_found'].format(
            idoklad_bank_account,
            idoklad_record["DocumentNumber"],
        )
    )


def convert_record_lines(idoklad_lines):
    lines = []

    for item in idoklad_lines:
        if "Code" in item and item["Code"] == "ZaokPol" and item["TotalPrice"] == 0:
            continue  # Skip artificial rounding item

        lines.append({
            "name": item["Name"],
            "quantity": item["Amount"],
            "unit_name": item["Unit"],
            "unit_price": item["UnitPrice"],
            "vat_rate": item["VatRate"],
        })

    return lines


def convert_invoice(
    idoklad_invoice,
    fakturoid_subject_id,
    fakturoid_payment_method,
    fakturoid_attachment,
    fakturoid_bank_account_id,
):
    result = {
        "number": idoklad_invoice["DocumentNumber"],
        "variable_symbol": idoklad_invoice["VariableSymbol"],
        "subject_id": fakturoid_subject_id,
        "order_number": idoklad_invoice["OrderNumber"],
        "issued_on": idoklad_invoice["DateOfIssue"],
        "taxable_fulfillment_due": idoklad_invoice["DateOfTaxing"],
        "due": idoklad_invoice["Maturity"],
        "note": idoklad_invoice["ItemsTextPrefix"],
        "footer_note": idoklad_invoice["ItemsTextSuffix"],
        "private_note": idoklad_invoice["Note"],
        "iban": idoklad_invoice["MyCompanyDocumentAddress"]["Iban"],
        "swift_bic": idoklad_invoice["MyCompanyDocumentAddress"]["Swift"],
        "payment_method": fakturoid_payment_method,
        "currency": idoklad_invoice["Currency"]["Code"],
        "exchange_rate": idoklad_invoice["ExchangeRate"],
        "language": idoklad_invoice["LanguageCode"].split("-")[1].lower(),
        "lines": convert_record_lines(idoklad_invoice['IssuedInvoiceItems']),
    }

    if fakturoid_bank_account_id:
        result["bank_account"] = fakturoid_bank_account_id

    if fakturoid_attachment:
        result["attachment"] = fakturoid_attachment

    return result


def convert_expense(
    idoklad_expense,
    fakturoid_subject_id,
    fakturoid_payment_method,
    fakturoid_attachment,
):
    result = {
        "number": idoklad_expense["DocumentNumber"].replace("DF", "N"),
        "original_number": idoklad_expense["ReceivedDocumentNumber"],
        "variable_symbol": idoklad_expense["VariableSymbol"],
        "subject_id": fakturoid_subject_id,
        "document_type": "invoice",
        "issued_on": idoklad_expense["DateOfReceiving"],
        "taxable_fulfillment_due": idoklad_expense["DateOfReceiving"],
        "due_on": idoklad_expense["DateOfPayment"],
        "description": idoklad_expense["Description"],
        "private_note": idoklad_expense["Note"],
        "payment_method": fakturoid_payment_method,
        "hide_bank_account": True,
        "currency": idoklad_expense["Currency"]["Code"],
        "exchange_rate": idoklad_expense["ExchangeRate"],
        "lines": convert_record_lines(idoklad_expense['Items']),
    }

    if fakturoid_attachment:
        result["attachment"] = fakturoid_attachment

    return result


def record_already_transfered(fakturoid_records, idoklad_number):
    for record in fakturoid_records:
        if record["number"] == idoklad_number:
            return True

    return False

def fakturoid_vat_matches_record_vat_or_continue(
    fakturoid_vat_no,
    record_vat_no,
    record_number,
    type,
):
    if fakturoid_vat_no == record_vat_no:
        return True
    
    print(
        "\nWARNING: Your Fakturoid VAT Number ({fakturoid_vat_no}) does not match the iDoklad {type} ({idoklad_invoice_number}) VAT Number ({idoklad_vat_no}). You can change it in the web app.".format(
            fakturoid_vat_no=fakturoid_vat_no,
            type=type,
            record_invoice_number=record_number,
            record_vat_no=record_vat_no,
        )
    )

    if input("Do you want to continue anyway? [y/n]") == "y":
        return True

    return False


def process_record(
    idoklad,
    idoklad_record,
    fakturoid,
    fakturoid_subjects,
    fakturoid_bank_accounts,
    type,
):
    if not type == "invoice" and not type == "expense":
        raise Exception(
            ERROR_MESSAGES['unknown_record_type'].format(type)
        )

    result = {}
    idoklad_subject_type = "Purchaser" if type == "invoice" else "Supplier"

    print(
        "--- Processing iDoklad {type} {number}".format(
            type=type,
            number=idoklad_record["DocumentNumber"],
        )
    )

    record_fakturoid_attachment = None

    if not idoklad_record["AttachmentFileName"] == "":
        print("Loading attachment")

        idoklad_attachment = idoklad.get_attachment(
            type,
            idoklad_record["Id"],
        )

        if idoklad_attachment:
            record_fakturoid_attachment = make_attachment(idoklad_attachment)

    record_fakturoid_subject_id = find_fakturoid_subject_id(
        fakturoid_subjects,
        idoklad_record[idoklad_subject_type],
    )

    if not record_fakturoid_subject_id:
        subject_type = 'customer' if type == 'invoice' else 'supplier'
        subject_object = make_subject(
            idoklad_record[idoklad_subject_type],
            subject_type,
        )
        fakturoid_subject = fakturoid.create_subject(subject_object)
        record_fakturoid_subject_id = fakturoid_subject["id"]
        result["fakturoid_subject"] = fakturoid_subject

    record_fakturoid_payment_method = find_fakturoid_payment_method(
        idoklad_record,
    )

    record_fakturoid_bank_account_id = None

    if record_fakturoid_payment_method == "B":
        record_fakturoid_bank_account_id = find_fakturoid_bank_account_id(
            fakturoid_bank_accounts,
            idoklad_record,
        )

    fakturoid_record = {}

    if type == 'invoice':
        fakturoid_record = fakturoid.create_invoice(
            convert_invoice(
                idoklad_record,
                record_fakturoid_subject_id,
                record_fakturoid_payment_method,
                record_fakturoid_attachment,
                record_fakturoid_bank_account_id,
            )
        )
    else:
        fakturoid_record = fakturoid.create_expense(
            convert_expense(
                idoklad_record,
                record_fakturoid_subject_id,
                record_fakturoid_payment_method,
                record_fakturoid_attachment,
            )
        )

    result["fakturoid_record"] = fakturoid_record

    print(
        "Created Fakturoid {type} {number}".format(
            type=type,
            number=fakturoid_record["number"],
        )
    )

    if not idoklad_record["DateOfPayment"] == "":
        payload = {}

        if type == "invoice":
            payload = { "paid_at": idoklad_record["DateOfPayment"] }
        else:
            payload = { "paid_on": idoklad_record["DateOfPayment"] }

        fakturoid.pay_record(type, fakturoid_record["id"], payload)

        print(
            "Paid Fakturoid {type} {number}".format(
                type=type,
                number=fakturoid_record["number"],
            )
        )

    return result
