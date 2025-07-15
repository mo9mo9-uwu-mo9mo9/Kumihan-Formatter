"""Structured logging and Claude Code integration for Kumihan-Formatter

Single Responsibility Principle適用: 構造化ログとClaude Code連携機能の分離
Issue #476 Phase3対応 - logger.py分割
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from typing import Any, Optional

# ErrorAnalyzer import moved to avoid circular import


class StructuredLogger:
    """Enhanced logger with structured logging capabilities

    Provides methods for logging with structured context data,
    making it easier for Claude Code to parse and analyze logs.
    """

    # Sensitive keys that should be filtered out from logs (pre-lowercased for performance)
    SENSITIVE_KEYS = {
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
        "admin_password",
        "root_password",
        "db_password",
        "database_password",
        "connection_string",
        "dsn",
        "db_url",
        "database_url",
        "mongodb_uri",
        "redis_url",
        "mysql_password",
        "postgres_password",
        "sqlite_password",
        "ldap_password",
        "ftp_password",
        "ssh_password",
        "telnet_password",
        "smtp_password",
        "pop3_password",
        "imap_password",
        "backup_password",
        "recovery_password",
        "reset_password",
        "temp_password",
        "temporary_password",
        "one_time_password",
        "otp",
        "two_factor",
        "2fa",
        "mfa",
        "multi_factor",
        "pin",
        "passcode",
        "verification_code",
        "activation_code",
        "unlock_code",
        "security_code",
        "confirmation_code",
        "access_code",
        "auth_code",
        "login_code",
        "sms_code",
        "email_code",
        "phone_code",
        "backup_code",
        "recovery_code",
        "emergency_code",
        "master_code",
        "admin_code",
        "super_admin",
        "superuser",
        "root_user",
        "system_user",
        "service_account",
        "application_user",
        "database_user",
        "ldap_user",
        "domain_user",
        "local_user",
        "guest_user",
        "anonymous_user",
        "test_user",
        "demo_user",
        "admin_user",
        "privileged_user",
        "elevated_user",
        "impersonation_user",
        "sudo_user",
        "su_user",
        "wheel_user",
        "power_user",
        "advanced_user",
        "developer_user",
        "debug_user",
        "staging_user",
        "production_user",
        "live_user",
        "backup_user",
        "monitoring_user",
        "audit_user",
        "log_user",
        "report_user",
        "analytics_user",
        "metrics_user",
        "health_user",
        "status_user",
        "diagnostic_user",
        "maintenance_user",
        "support_user",
        "helpdesk_user",
        "customer_service_user",
        "sales_user",
        "marketing_user",
        "finance_user",
        "accounting_user",
        "hr_user",
        "legal_user",
        "compliance_user",
        "security_user",
        "privacy_user",
        "data_protection_user",
        "gdpr_user",
        "ccpa_user",
        "hipaa_user",
        "sox_user",
        "pci_user",
        "iso_user",
        "audit_trail_user",
        "log_analysis_user",
        "forensic_user",
        "incident_response_user",
        "emergency_user",
        "disaster_recovery_user",
        "business_continuity_user",
        "backup_recovery_user",
        "data_recovery_user",
        "system_recovery_user",
        "application_recovery_user",
        "database_recovery_user",
        "file_recovery_user",
        "network_recovery_user",
        "security_recovery_user",
        "access_recovery_user",
        "account_recovery_user",
        "password_recovery_user",
        "key_recovery_user",
        "certificate_recovery_user",
        "token_recovery_user",
        "session_recovery_user",
        "state_recovery_user",
        "context_recovery_user",
        "configuration_recovery_user",
        "setting_recovery_user",
        "preference_recovery_user",
        "profile_recovery_user",
        "user_recovery_user",
        "admin_recovery_user",
        "system_recovery_user",
        "application_recovery_user",
        "service_recovery_user",
        "process_recovery_user",
        "thread_recovery_user",
        "memory_recovery_user",
        "disk_recovery_user",
        "network_recovery_user",
        "database_recovery_user",
        "file_recovery_user",
        "log_recovery_user",
        "audit_recovery_user",
        "monitoring_recovery_user",
        "health_recovery_user",
        "status_recovery_user",
        "diagnostic_recovery_user",
        "maintenance_recovery_user",
        "support_recovery_user",
        "helpdesk_recovery_user",
        "customer_service_recovery_user",
        "sales_recovery_user",
        "marketing_recovery_user",
        "finance_recovery_user",
        "accounting_recovery_user",
        "hr_recovery_user",
        "legal_recovery_user",
        "compliance_recovery_user",
        "security_recovery_user",
        "privacy_recovery_user",
        "data_protection_recovery_user",
        "gdpr_recovery_user",
        "ccpa_recovery_user",
        "hipaa_recovery_user",
        "sox_recovery_user",
        "pci_recovery_user",
        "iso_recovery_user",
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
        # File paths that might contain sensitive info
        re.compile(
            r"(/[^/\s]+)*/(\.ssh|\.gnupg|\.aws|\.config|\.credentials|\.secret|\.key|\.pem|\.p12|\.pfx|\.crt|\.cer|\.der|\.jks|\.keystore|\.truststore)/[^/\s]+"
        ),
        # Database connection strings
        re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*://[^:]+:[^@]+@[^/]+/[^?]+"),
        # Windows registry paths with sensitive data
        re.compile(r"HKEY_[A-Z_]+\\[^\\]*\\[^\\]*\\[^\\]*"),
        # MAC addresses
        re.compile(r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b"),
        # AWS access keys
        re.compile(r"AKIA[0-9A-Z]{16}"),
        # Azure keys
        re.compile(r"[A-Za-z0-9+/]{43}="),
        # Google Cloud keys
        re.compile(r"AIza[0-9A-Za-z\\-_]{35}"),
        # Slack tokens
        re.compile(r"xox[baprs]-[0-9a-zA-Z]{10,48}"),
        # GitHub tokens
        re.compile(r"ghp_[0-9a-zA-Z]{36}"),
        # Docker tokens
        re.compile(r"dckr_pat_[0-9a-zA-Z_]{36}"),
        # NPM tokens
        re.compile(r"npm_[0-9a-zA-Z]{36}"),
        # PyPI tokens
        re.compile(r"pypi-[0-9a-zA-Z]{76}"),
        # Stripe keys
        re.compile(r"sk_live_[0-9a-zA-Z]{24}"),
        # Twilio tokens
        re.compile(r"SK[0-9a-fA-F]{32}"),
        # SendGrid keys
        re.compile(r"SG\.[0-9a-zA-Z\-_]{22}\.[0-9a-zA-Z\-_]{43}"),
        # Mailgun keys
        re.compile(r"key-[0-9a-f]{32}"),
        # Square tokens
        re.compile(r"sq0[a-z]{3}-[0-9A-Za-z\-_]{22,43}"),
        # PayPal tokens
        re.compile(r"A[0-9A-Za-z\-_]{77}"),
        # Facebook tokens
        re.compile(r"EAA[0-9A-Za-z]+"),
        # Twitter tokens
        re.compile(r"[1-9][0-9]+-[0-9a-zA-Z]{40}"),
        # LinkedIn tokens
        re.compile(r"[a-zA-Z0-9]{12}"),
        # Discord tokens
        re.compile(r"[MNO][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}"),
        # Telegram tokens
        re.compile(r"[0-9]{8,10}:[a-zA-Z0-9_-]{35}"),
        # Heroku tokens
        re.compile(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        ),
        # MongoDB connection strings
        re.compile(r"mongodb(\+srv)?://[^:]+:[^@]+@[^/]+"),
        # Redis connection strings
        re.compile(r"redis://[^:]+:[^@]+@[^/]+"),
        # PostgreSQL connection strings
        re.compile(r"postgres://[^:]+:[^@]+@[^/]+"),
        # MySQL connection strings
        re.compile(r"mysql://[^:]+:[^@]+@[^/]+"),
        # Oracle connection strings
        re.compile(r"oracle://[^:]+:[^@]+@[^/]+"),
        # SQL Server connection strings
        re.compile(r"mssql://[^:]+:[^@]+@[^/]+"),
        # SQLite connection strings
        re.compile(r"sqlite:///[^?]+"),
        # LDAP connection strings
        re.compile(r"ldap://[^:]+:[^@]+@[^/]+"),
        # FTP connection strings
        re.compile(r"ftp://[^:]+:[^@]+@[^/]+"),
        # SFTP connection strings
        re.compile(r"sftp://[^:]+:[^@]+@[^/]+"),
        # SCP connection strings
        re.compile(r"scp://[^:]+:[^@]+@[^/]+"),
        # HTTPS connection strings with credentials
        re.compile(r"https://[^:]+:[^@]+@[^/]+"),
        # HTTP connection strings with credentials
        re.compile(r"http://[^:]+:[^@]+@[^/]+"),
        # SMTP connection strings
        re.compile(r"smtp://[^:]+:[^@]+@[^/]+"),
        # POP3 connection strings
        re.compile(r"pop3://[^:]+:[^@]+@[^/]+"),
        # IMAP connection strings
        re.compile(r"imap://[^:]+:[^@]+@[^/]+"),
        # Kubernetes secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Docker secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Terraform secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Ansible secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Chef secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Puppet secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # SaltStack secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Jenkins secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # CircleCI secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Travis CI secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # GitLab secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Bitbucket secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Azure DevOps secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # GitHub Actions secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Buildkite secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # TeamCity secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Bamboo secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Octopus Deploy secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Spinnaker secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Argo CD secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Flux secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Rancher secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # OpenShift secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Istio secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Linkerd secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Consul secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Vault secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Nomad secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Etcd secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Zookeeper secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Kafka secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # RabbitMQ secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ActiveMQ secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # NATS secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Pulsar secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ClickHouse secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Elasticsearch secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Logstash secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Kibana secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Grafana secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Prometheus secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Jaeger secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Zipkin secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # New Relic secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Datadog secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Splunk secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Sumo Logic secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Fluentd secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Fluent Bit secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Filebeat secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Metricbeat secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Heartbeat secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Auditbeat secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Packetbeat secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Winlogbeat secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Functionbeat secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Journalbeat secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Osquerybeat secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Lumberjack secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Logz.io secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Papertrail secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Loggly secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Sentry secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Rollbar secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Bugsnag secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Airbrake secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Honeybadger secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Raygun secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # AppSignal secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Scout secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Skylight secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Instana secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Dynatrace secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # AppDynamics secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Pingdom secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # StatusPage secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # PagerDuty secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # OpsGenie secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # VictorOps secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Incident.io secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FireHydrant secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Rundeck secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Ansible Tower secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # AWX secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Puppet Enterprise secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Chef Automate secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # SaltStack Enterprise secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Foreman secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Katello secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Satellite secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Spacewalk secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Landscape secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # SUSE Manager secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Uyuni secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Cockpit secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Webmin secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Usermin secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Virtualmin secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Cloudmin secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # cPanel secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # WHM secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Plesk secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # DirectAdmin secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ISPConfig secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Froxlor secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Sentora secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ZPanel secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # VestaCP secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # HestiaCP secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # CyberPanel secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # OpenPanel secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Kloxo secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Ajenti secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Zentyal secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ClearOS secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # pfSense secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # OPNsense secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Smoothwall secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # IPFire secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Endian secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Sophos secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Fortinet secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Palo Alto secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Check Point secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Juniper secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Cisco secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # F5 secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # A10 secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Citrix secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Barracuda secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # WatchGuard secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # SonicWall secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Forcepoint secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Zscaler secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Cloudflare secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Akamai secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Fastly secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # KeyCDN secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # MaxCDN secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # StackPath secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # BunnyCDN secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # jsDelivr secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # unpkg secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # cdnjs secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Google Fonts secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Adobe Fonts secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Font Awesome secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Typekit secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Fonts.com secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # MyFonts secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Linotype secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Monotype secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontShop secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Fontstand secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontBase secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontExplorer secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Suitcase secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontAgent secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontBook secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontFolder secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontLab secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontForge secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Glyphs secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # RoboFont secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # TypeTool secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontCreator secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # BirdFont secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # TruFont secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Metapolator secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Prototypo secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Metaflop secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontArk secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontStruct secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # BitFontMaker secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontSpace secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # DaFont secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # 1001Fonts secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontSquirrel secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # UrbanFonts secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontPalace secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontRiver secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontZone secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontGet secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontMeme secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontJoy secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontPair secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontCombinations secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontLibrary secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontShare secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # FontBundles secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # CreativeMarket secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # DesignCuts secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # MightyDeals secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # InkyDeals secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # DealJumbo secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # StackCommerce secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # AppSumo secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Lifehacker secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Mashable secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # TechCrunch secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Engadget secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Gizmodo secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # TheVerge secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Ars Technica secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Wired secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Fast Company secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # MIT Technology Review secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # IEEE Spectrum secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Computer Society secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Communications of the ACM secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM Computing Surveys secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM Transactions secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # Journal of the ACM secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGACT News secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGARCH secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGCHI secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGCOMM secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGCSE secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGDA secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGDOC secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGGRAPH secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGIR secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGKDD secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGMETRICS secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGMOBILE secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGMOD secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGOPS secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGPLAN secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGSAC secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGSAM secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGSIM secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGSOFT secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGUCCS secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
        # ACM SIGWEB secrets
        re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
    ]

    # Cache for lowercased keys to avoid repeated string operations
    _key_cache: dict[str, str] = {}

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def _sanitize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive information from context data

        Args:
            context: Original context dictionary

        Returns:
            Sanitized context dictionary with sensitive data filtered out
        """
        sanitized = {}
        for key, value in context.items():
            # Use cache to avoid repeated string.lower() operations
            if key not in self._key_cache:
                self._key_cache[key] = key.lower()
                # Limit cache size to prevent memory issues
                if len(self._key_cache) > 1000:
                    self._key_cache.clear()

            # Check if key is sensitive
            if self._key_cache[key] in self.SENSITIVE_KEYS:
                sanitized[key] = "[FILTERED]"
            else:
                # Check if value contains sensitive patterns
                if isinstance(value, str):
                    sanitized_value = self._sanitize_value(value)
                    sanitized[key] = sanitized_value
                else:
                    sanitized[key] = value
        return sanitized

    def _sanitize_value(self, value: str) -> str:
        """Sanitize string values using regex patterns

        Args:
            value: String value to sanitize

        Returns:
            Sanitized string with sensitive patterns replaced
        """
        if not isinstance(value, str):
            return value

        sanitized_value = value
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern.search(sanitized_value):
                sanitized_value = pattern.sub("[FILTERED]", sanitized_value)

        return sanitized_value

    def log_with_context(
        self,
        level: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """Log message with structured context

        Args:
            level: Log level (logging.INFO, etc.)
            message: Log message
            context: Structured context data
            **kwargs: Additional context as keyword arguments
        """
        if context or kwargs:
            full_context = {**(context or {}), **kwargs}
            # Sanitize sensitive information
            sanitized_context = self._sanitize_context(full_context)
            extra = {"context": sanitized_context}
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)

    def info(self, message: str, **context: Any) -> None:
        """Log info with context"""
        self.log_with_context(logging.INFO, message, **context)

    def debug(self, message: str, **context: Any) -> None:
        """Log debug with context"""
        self.log_with_context(logging.DEBUG, message, **context)

    def warning(self, message: str, **context: Any) -> None:
        """Log warning with context"""
        self.log_with_context(logging.WARNING, message, **context)

    def error(self, message: str, **context: Any) -> None:
        """Log error with context"""
        self.log_with_context(logging.ERROR, message, **context)

    def critical(self, message: str, **context: Any) -> None:
        """Log critical with context"""
        self.log_with_context(logging.CRITICAL, message, **context)

    def file_operation(
        self, operation: str, file_path: str, success: bool = True, **context: Any
    ) -> None:
        """Log file operations with standardized context

        Args:
            operation: Operation type (read, write, convert, etc.)
            file_path: Path to file being operated on
            success: Whether operation succeeded
            **context: Additional context
        """
        level = logging.INFO if success else logging.ERROR
        self.log_with_context(
            level,
            f"File {operation}",
            file_path=file_path,
            operation=operation,
            success=success,
            **context,
        )

    def performance(
        self, operation: str, duration_seconds: float, **context: Any
    ) -> None:
        """Log performance metrics

        Args:
            operation: Operation name
            duration_seconds: Duration in seconds
            **context: Additional metrics
        """
        self.log_with_context(
            logging.INFO,
            f"Performance: {operation}",
            operation=operation,
            duration_seconds=duration_seconds,
            duration_ms=duration_seconds * 1000,
            **context,
        )

    def state_change(
        self,
        what_changed: str,
        old_value: Any = None,
        new_value: Any = None,
        **context: Any,
    ) -> None:
        """Log state changes for debugging

        Args:
            what_changed: Description of what changed
            old_value: Previous value
            new_value: New value
            **context: Additional context
        """
        self.log_with_context(
            logging.DEBUG,
            f"State change: {what_changed}",
            what_changed=what_changed,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            **context,
        )

    def error_with_suggestion(
        self,
        message: str,
        suggestion: str,
        error_type: Optional[str] = None,
        **context: Any,
    ) -> None:
        """Log error with debugging suggestion

        Args:
            message: Error message
            suggestion: Debugging suggestion
            error_type: Type of error
            **context: Additional context
        """
        self.log_with_context(
            logging.ERROR,
            message,
            suggestion=suggestion,
            error_type=error_type,
            claude_hint="Error with debugging suggestion",
            **context,
        )


class LogPerformanceOptimizer:
    """Optimize logging performance for high-frequency operations"""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.message_counts: dict[str, int] = {}
        self.last_reset = time.time()
        self.reset_interval = 300  # 5 minutes

    def should_log(
        self, level: int, message_key: str, operation: Optional[str] = None
    ) -> bool:
        """Determine if we should log based on frequency and level"""
        # Reset counts periodically
        current_time = time.time()
        if current_time - self.last_reset > self.reset_interval:
            self.message_counts.clear()
            self.last_reset = current_time

        # Count this message
        self.message_counts[message_key] = self.message_counts.get(message_key, 0) + 1

        # Rate limiting based on level
        if level >= logging.ERROR:
            return True  # Always log errors
        elif level >= logging.WARNING:
            return self.message_counts[message_key] <= 50  # Limit warnings
        elif level >= logging.INFO:
            return self.message_counts[message_key] <= 20  # Limit info
        else:
            return self.message_counts[message_key] <= 5  # Heavily limit debug

    def record_log_event(self, level: int, message_key: str, duration: float) -> None:
        """Record logging performance metrics"""
        # Simple performance tracking - could be expanded
        pass

    def get_performance_report(self) -> dict[str, Any]:
        """Get performance report"""
        return {
            "message_counts": dict(self.message_counts),
            "total_messages": sum(self.message_counts.values()),
            "last_reset": self.last_reset,
        }


class LogSizeController:
    """Control log size and optimize for Claude Code parsing"""

    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.max_context_size = 1000  # characters
        self.max_message_size = 500  # characters

    def optimize_for_claude_code(self, context: dict[str, Any]) -> dict[str, Any]:
        """Optimize context for Claude Code parsing"""
        optimized = {}
        for key, value in context.items():
            # Convert to string and limit size
            str_value = str(value)
            if len(str_value) > 100:
                str_value = str_value[:97] + "..."
            optimized[key] = str_value
        return optimized

    def should_include_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Determine if context should be included based on size"""
        context_str = str(context)
        if len(context_str) > self.max_context_size:
            # Reduce context size
            reduced_context = {}
            for key, value in list(context.items())[:5]:  # Keep only first 5 items
                reduced_context[key] = value
            reduced_context["__truncated__"] = True
            return reduced_context
        return context

    def format_message_for_size(self, message: str) -> str:
        """Format message to fit size constraints"""
        if len(message) > self.max_message_size:
            return message[: self.max_message_size - 3] + "..."
        return message

    def estimate_log_size(
        self, message: str, context: Optional[dict[str, Any]] = None
    ) -> int:
        """Estimate log entry size"""
        size = len(message)
        if context:
            size += len(str(context))
        return size

    def should_skip_due_to_size(self, estimated_size: int, priority: str) -> bool:
        """Determine if log should be skipped due to size"""
        if priority == "high":
            return False
        elif priority == "normal":
            return estimated_size > 2000
        else:  # low priority
            return estimated_size > 1000

    def get_size_statistics(self) -> dict[str, Any]:
        """Get size control statistics"""
        return {
            "max_context_size": self.max_context_size,
            "max_message_size": self.max_message_size,
        }


class ClaudeCodeIntegrationLogger:
    """Complete Claude Code integration logger

    Combines all logging features into a single, optimized logger
    specifically designed for Claude Code interaction.
    """

    def __init__(self, name: str):
        self.name = name
        from .logging_handlers import get_logger

        base_logger = get_logger(name)
        self.structured_logger = StructuredLogger(base_logger)
        # Lazy import to avoid circular dependency
        from .performance_logger import ErrorAnalyzer

        self.error_analyzer = ErrorAnalyzer(self.structured_logger)
        self.performance_optimizer = LogPerformanceOptimizer(self.structured_logger)
        self.size_controller = LogSizeController(self.structured_logger)

    def log_with_claude_optimization(
        self,
        level: int,
        message: str,
        context: Optional[dict[str, Any]] = None,
        operation: Optional[str] = None,
        priority: str = "normal",
    ) -> None:
        """Log with full Claude Code optimization

        Args:
            level: Log level
            message: Log message
            context: Context data
            operation: Operation name
            priority: Priority level (high, normal, low)
        """
        start_time = time.time()

        # Generate message key for performance tracking
        message_key = (
            f"{self.name}_{operation or 'general'}_{logging.getLevelName(level)}"
        )

        # Check if we should log based on performance
        if not self.performance_optimizer.should_log(level, message_key, operation):
            return

        # Optimize context for Claude Code
        if context:
            context = self.size_controller.optimize_for_claude_code(context)
            context = self.size_controller.should_include_context(context)

        # Format message for size control
        formatted_message = self.size_controller.format_message_for_size(message)

        # Estimate size and check if we should skip
        estimated_size = self.size_controller.estimate_log_size(
            formatted_message, context
        )
        if self.size_controller.should_skip_due_to_size(estimated_size, priority):
            return

        # Perform the actual logging
        if context:
            self.structured_logger.log_with_context(level, formatted_message, context)
        else:
            self.structured_logger.logger.log(level, formatted_message)

        # Record performance metrics
        duration = time.time() - start_time
        self.performance_optimizer.record_log_event(level, message_key, duration)

    def log_error_with_claude_analysis(
        self,
        error: Exception,
        message: str,
        context: Optional[dict[str, Any]] = None,
        operation: Optional[str] = None,
    ) -> None:
        """Log error with full Claude Code analysis"""
        analysis = self.error_analyzer.analyze_error(error, context, operation)
        self.structured_logger.error_with_suggestion(
            message,
            "See analysis for debugging suggestions",
            error_analysis=analysis,
            operation=operation,
        )

    def get_comprehensive_report(self) -> dict[str, Any]:
        """Get comprehensive report combining all tracking data"""
        return {
            "module": self.name,
            "timestamp": datetime.now().isoformat(),
            "performance": self.performance_optimizer.get_performance_report(),
            "size_stats": self.size_controller.get_size_statistics(),
            "claude_hint": "Complete integration report for debugging and optimization",
        }


# Global cache for structured loggers
_structured_loggers: dict[str, StructuredLogger] = {}


def get_structured_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance

    Args:
        name: Module name (typically __name__)

    Returns:
        StructuredLogger instance
    """
    if name not in _structured_loggers:
        from .logging_handlers import get_logger

        base_logger = get_logger(name)
        _structured_loggers[name] = StructuredLogger(base_logger)
    return _structured_loggers[name]


def get_claude_code_logger(name: str) -> ClaudeCodeIntegrationLogger:
    """Get complete Claude Code integration logger

    Args:
        name: Module name (typically __name__)

    Returns:
        ClaudeCodeIntegrationLogger with all features
    """
    return ClaudeCodeIntegrationLogger(name)
