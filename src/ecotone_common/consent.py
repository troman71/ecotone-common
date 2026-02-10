"""Consent logging helpers.

No Flask dependency. Caller provides a DB cursor.
Tables (consent_log, eula_versions) must exist in the app's database.
"""


def log_consent(cursor, user_id, consent_type: str, version: str,
                accepted: bool, ip_address: str = None, user_agent: str = None):
    """Insert a row into the consent_log table."""
    cursor.execute(
        """INSERT INTO consent_log
           (user_id, consent_type, version, accepted, ip_address, user_agent)
           VALUES (%s, %s, %s, %s, %s::inet, %s)""",
        (user_id, consent_type, version, accepted, ip_address, user_agent)
    )


def get_current_eula_version(cursor) -> str | None:
    """Return the latest EULA version string, or None if no versions exist."""
    cursor.execute(
        "SELECT version FROM eula_versions ORDER BY effective_date DESC LIMIT 1"
    )
    row = cursor.fetchone()
    if row is None:
        return None
    # Support both dict-like and tuple cursors
    if isinstance(row, dict):
        return row['version']
    return row[0]
