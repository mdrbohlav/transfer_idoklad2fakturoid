# transfer_idoklad2fakturoid
Transfer invoices, expenses and contacts from iDoklad to Fakturoid.

Usage:
```
./main.py --fakturoid-account [...] --fakturoid-email [...] --fakturoid-api-key [...] --idoklad-client-id [...] --idoklad-client-secret [...] --idoklad-filter [...] --disable-vat-number-check --export-idoklad-as-pdf
```

More about filters can be found here: https://api.idoklad.cz/Help/v2/, enter it like this `--idoklad-filter DateOfIssue~gt~2018-12-31`.

Arguments:
```
--fakturoid-account [...]     | Your Fatkuroid account slug.
--fakturoid-email [...]       | Your Fakturoid e-mail.
--fakturoid-api-key [...]     | Your Fakturoid API key.
--idoklad-client-id [...]     | Your iDoklad Client ID.
--idoklad-client-secret [...] | Your iDoklad Client Secret.
--idoklad-filter [...]        | Optional. iDoklad filter (eg. DateOfIssue~gt~2018-12-31).
--disable-vat-number-check    | Disabled the VAT number check for your Fakturoid account and each iDoklad invoice and expense.
--export-idoklad-as-pdf       | Export the iDoklad invoices and expenses as PDF.
```
