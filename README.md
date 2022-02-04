# transfer_idoklad2fakturoid
Transfer invoices, expenses and contacts from iDoklad to Fakturoid.

Usage:
```
./main.py --fakturoid-account [...] --fakturoid-email [...] --fakturoid-api-key [...] --idoklad-client-id [...] --idoklad-client-secret [...] --idoklad-filter [...] --disable-vat-number-check
```

More about filters can be found here: https://api.idoklad.cz/Help/v2/, enter it like this `--idoklad-filter DateOfIssue~gt~2018-12-31`.
