import re

class PIIFilter:
    def __init__(self):
        self.patterns = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'credit_card': r'\b(?:\d[ -]*?){13,16}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'api_key': r'sk-[a-zA-Z0-9]{32,}'
        }

    def mask(self, text: str) -> str:
        """
        Masks PII in the given text.
        """
        masked_text = text
        for name, pattern in self.patterns.items():
            masked_text = re.sub(pattern, f'<{name.upper()}_REDACTED>', masked_text)
        return masked_text
