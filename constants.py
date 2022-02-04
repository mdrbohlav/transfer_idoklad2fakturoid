CACHE_FILE = "transfer_idoklad2fakturoid.cache"
PAYMENT_METHOD_IDOKLAD_TO_FAKTUROID = {
    "B": "bank",
    "H": "cash",
    "D": "cod",
    "PP": "paypal",
    "P": "card",
}
ERROR_MESSAGES = {
    "request_failed": "{} {} failed with code {}\n\n{}",
    "unknown_payment_method": "Unknown iDoklad payment method code: {}, record number: {}",
    "bank_account_not_found": "Unknown iDoklad bank account: {}, record number: {}",
    "unknown_record_type": "Unknown record type: {}",
}
