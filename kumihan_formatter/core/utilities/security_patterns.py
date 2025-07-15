"""Security patterns and sensitive data detection for logging

Single Responsibility Principle適用: セキュリティパターンとセンシティブデータ検出の分離
Issue #476 Phase3対応 - structured_logger.py分割
"""

import re
from typing import Set

# Sensitive keys that should be filtered out from logs (pre-lowercased for performance)
SENSITIVE_KEYS: Set[str] = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "key",
    "api_key",
    "auth_token",
    "bearer_token",
    "access_token",
    "refresh_token",
    "credential",
    "credentials",
    "authorization",
    "session_id",
    "cookie",
    "private_key",
    "public_key",
    "cert",
    "certificate",
    "signature",
    "hash",
    "salt",
    "nonce",
    "jwt",
    "oauth",
    "basic_auth",
    "digest_auth",
    "x_api_key",
    "x_auth_token",
    "x_access_token",
    "user_agent",
    "referer",
    "x_forwarded_for",
    "x_real_ip",
    "client_ip",
    "remote_addr",
    "email",
    "username",
    "user_id",
    "account_id",
    "personal_info",
    "pii",
    "ssn",
    "social_security",
    "credit_card",
    "card_number",
    "cvv",
    "expiry",
    "bank_account",
    "routing_number",
    "account_number",
    "phone_number",
    "mobile",
    "address",
    "postal_code",
    "zip_code",
    "date_of_birth",
    "dob",
    "license_number",
    "passport_number",
    "national_id",
    "driver_license",
    "health_record",
    "medical_record",
    "biometric",
    "fingerprint",
    "face_id",
    "voice_print",
    "location",
    "gps",
    "lat",
    "lng",
    "latitude",
    "longitude",
    "geolocation",
    "ip_address",
    "mac_address",
    "device_id",
    "imei",
    "uuid",
    "guid",
    "session_token",
    "csrf_token",
    "xsrf_token",
    "api_secret",
    "client_secret",
    "webhook_secret",
    "encryption_key",
    "decryption_key",
    "shared_secret",
    "master_key",
    "root_key",
    "private_data",
    "confidential",
    "sensitive",
    "classified",
    "restricted",
    "internal",
    "proprietary",
    "personal",
    "private",
    "protected",
    "secure",
}

# Regex patterns for sensitive data values
SENSITIVE_PATTERNS = [
    # Email addresses
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    # Phone numbers (various formats)
    re.compile(r"(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"),
    # Credit card numbers
    re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    # Social Security Numbers
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # IP addresses
    re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
    # URLs with credentials
    re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^:]+:[^@]+@[^/]+"),
    # JWT tokens
    re.compile(r"eyJ[A-Za-z0-9+/]*\.eyJ[A-Za-z0-9+/]*\.[A-Za-z0-9+/]*"),
    # Base64 encoded strings (likely keys/tokens)
    re.compile(r"[A-Za-z0-9+/]{32,}={0,2}"),
    # Hex strings (likely keys/hashes)
    re.compile(r"\b[0-9a-fA-F]{32,}\b"),
    # UUIDs
    re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
    # API keys (common patterns)
    re.compile(r"[A-Za-z0-9]{20,}"),
    # AWS access keys
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # GitHub tokens
    re.compile(r"ghp_[0-9a-zA-Z]{36}"),
    # Slack tokens
    re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"),
]


class SecurityPatternMatcher:
    """Utility class for matching security patterns in log data"""

    # Cache for lowercased keys to avoid repeated string operations
    _key_cache: dict[str, str] = {}

    @classmethod
    def is_sensitive_key(cls, key: str) -> bool:
        """Check if a key is sensitive

        Args:
            key: The key to check

        Returns:
            True if the key is sensitive
        """
        # Use cache to avoid repeated string.lower() operations
        if key not in cls._key_cache:
            cls._key_cache[key] = key.lower()
            # Limit cache size to prevent memory issues
            if len(cls._key_cache) > 1000:
                cls._key_cache.clear()

        return cls._key_cache[key] in SENSITIVE_KEYS

    @classmethod
    def sanitize_value(cls, value: str) -> str:
        """Sanitize string values using regex patterns

        Args:
            value: String value to sanitize

        Returns:
            Sanitized string with sensitive patterns replaced
        """
        if not isinstance(value, str):
            return value

        sanitized_value = value
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(sanitized_value):
                sanitized_value = pattern.sub("[FILTERED]", sanitized_value)

        return sanitized_value
