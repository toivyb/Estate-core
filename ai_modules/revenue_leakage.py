def detect_leakage(rents, expected_total):
    actual = sum(rents)
    if actual < expected_total * 0.95:
        return "Possible Undercharge"
    return "No Issue"
