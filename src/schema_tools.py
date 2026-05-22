"""
schema utilities for retrieval experiments.

chinook only has 11 tables, too small to show why retrieval matters.
so we generate decoy tables to simulate a big, messy database, then
later we'll retrieve only the relevant tables per question.
"""

from src.db import get_schema, DB_PATH
import sqlite3


# fake table names that sound plausible in a music/media company db
# but are NOT in chinook and are irrelevant to our eval questions.
DECOY_TABLE_NAMES = [
    "MarketingCampaign", "AdImpression", "EmailLog", "WebSession",
    "PageView", "ServerLog", "FeatureFlag", "ExperimentVariant",
    "SupportTicket", "TicketComment", "Subscription", "PaymentMethod",
    "Refund", "TaxRate", "ShippingZone", "Warehouse", "InventoryItem",
    "Vendor", "PurchaseOrder", "AuditLog", "UserPreference", "DeviceToken",
    "PushNotification", "Survey", "SurveyResponse", "AbTest",
    "RecommendationModel", "PlaylistFollower", "SocialShare", "Comment",
]


def _make_decoy_schema(name: str) -> str:
    """Generate a plausible-looking CREATE TABLE statement for a decoy."""
    return (
        f"CREATE TABLE [{name}]\n(\n"
        f"    [{name}Id] INTEGER PRIMARY KEY,\n"
        f"    [CreatedAt] DATETIME,\n"
        f"    [UpdatedAt] DATETIME,\n"
        f"    [Status] NVARCHAR(50),\n"
        f"    [Metadata] NVARCHAR(500)\n"
        f");"
    )


def get_real_table_schemas() -> dict[str, str]:
    """
    Return {table_name: create_statement} for the REAL chinook tables.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, sql FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        return {name: sql for name, sql in cursor.fetchall() if sql}


def get_all_table_schemas(include_decoys: bool = True) -> dict[str, str]:
    """
    Return {table_name: create_statement} for real tables + optional decoys.
    This simulates a big database where most tables are irrelevant.
    """
    schemas = get_real_table_schemas()
    if include_decoys:
        for name in DECOY_TABLE_NAMES:
            schemas[name] = _make_decoy_schema(name)
    return schemas


def full_schema_string(include_decoys: bool = True) -> str:
    """The 'dump everything' baseline: all tables concatenated."""
    schemas = get_all_table_schemas(include_decoys)
    return "\n\n".join(schemas.values())


if __name__ == "__main__":
    real = get_real_table_schemas()
    allt = get_all_table_schemas(include_decoys=True)
    print(f"real tables: {len(real)}")
    print(f"with decoys: {len(allt)}")
    full = full_schema_string(include_decoys=True)
    print(f"full schema chars: {len(full)} (~{len(full)//4} tokens)")