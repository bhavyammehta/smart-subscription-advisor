
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SUBSCRIPTIONS_FILE = DATA_DIR / "subscriptions.csv"

COLUMNS = [
    "id",
    "name",
    "category",
    "billing_cycle",
    "price",
    "usage_days",
    "importance",
    "alternatives",
    "cancellation_fee",
]

CATEGORIES = [
    "Entertainment",
    "Music",
    "Technology",
    "Fitness",
    "Education",
    "Health",
    "Lifestyle",
    "Other",
]


def validate_subscription(record):
    """Validate one subscription record."""

    name = str(record.get("name", "")).strip()
    category = str(record.get("category", "")).strip()
    cycle = str(record.get("billing_cycle", "")).strip()

    if not name:
        raise ValueError("Subscription name cannot be empty.")

    if category not in CATEGORIES:
        raise ValueError("Please select a valid category.")

    if cycle not in ("Monthly", "Annual"):
        raise ValueError("Billing cycle must be Monthly or Annual.")

    numeric_ranges = {
        "price": (0, 24000),
        "usage_days": (0, 30),
        "importance": (0, 10),
        "alternatives": (0, 10),
        "cancellation_fee": (0, 1000),
    }

    for field, (minimum, maximum) in numeric_ranges.items():
        value = record.get(field)

        if isinstance(value, bool):
            raise ValueError(f"{field} must be numeric.")

        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field} must be numeric.")

        if not pd.notna(number) or not minimum <= number <= maximum:
            raise ValueError(
                f"{field} must be between {minimum} and {maximum}."
            )

        if field == "usage_days" and not number.is_integer():
            raise ValueError("Usage days must be a whole number.")

    if float(record["price"]) <= 0:
        raise ValueError("Price must be greater than zero.")


def load_subscriptions():
    """Load subscription records from CSV."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not SUBSCRIPTIONS_FILE.exists():
        return pd.DataFrame(columns=COLUMNS)

    df = pd.read_csv(SUBSCRIPTIONS_FILE)

    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            f"Subscriptions CSV is missing columns: {sorted(missing)}"
        )

    df = df[COLUMNS].copy()

    if df["id"].duplicated().any():
        raise ValueError("Duplicate subscription IDs found in CSV.")

    return df


def save_subscriptions(df):
    """Validate and save all records."""

    if not set(COLUMNS).issubset(df.columns):
        raise ValueError("Subscription data has missing columns.")

    clean_df = df[COLUMNS].copy()

    if clean_df["id"].isna().any() or clean_df["id"].duplicated().any():
        raise ValueError("Subscription IDs must be unique and non-empty.")

    for _, row in clean_df.iterrows():
        validate_subscription(row.to_dict())

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(SUBSCRIPTIONS_FILE, index=False)


def add_subscription(record):
    """Add a new subscription and return its ID."""

    validate_subscription(record)
    df = load_subscriptions()

    name = str(record["name"]).strip()

    # Prevent accidental duplicate submissions by name.
    if df["name"].astype(str).str.casefold().eq(
        name.casefold()
    ).any():
        raise ValueError(
            "A subscription with this name already exists."
        )

    existing_numbers = []

    for subscription_id in df["id"].astype(str):
        if subscription_id.startswith("S"):
            try:
                existing_numbers.append(int(subscription_id[1:]))
            except ValueError:
                pass

    next_number = max(existing_numbers, default=0) + 1
    new_id = f"S{next_number:03d}"

    while new_id in df["id"].astype(str).tolist():
        next_number += 1
        new_id = f"S{next_number:03d}"

    new_record = {
        "id": new_id,
        "name": name,
        "category": record["category"],
        "billing_cycle": record["billing_cycle"],
        "price": float(record["price"]),
        "usage_days": int(record["usage_days"]),
        "importance": float(record["importance"]),
        "alternatives": float(record["alternatives"]),
        "cancellation_fee": float(record["cancellation_fee"]),
    }

    updated_df = pd.concat(
        [df, pd.DataFrame([new_record])],
        ignore_index=True,
    )

    save_subscriptions(updated_df)
    return new_id


def edit_subscription(subscription_id, updates):
    """Edit an existing subscription."""

    df = load_subscriptions()
    matches = df.index[df["id"] == subscription_id].tolist()

    if not matches:
        raise ValueError("Subscription ID was not found.")

    index = matches[0]
    updated_record = df.loc[index].to_dict()
    updated_record.update(updates)
    updated_record["name"] = str(
        updated_record["name"]
    ).strip()

    validate_subscription(updated_record)

    duplicate_names = (
        df.drop(index=index)["name"]
        .astype(str)
        .str.casefold()
        .eq(updated_record["name"].casefold())
    )

    if duplicate_names.any():
        raise ValueError(
            "Another subscription already uses this name."
        )

    for field in COLUMNS:
        if field != "id":
            df.at[index, field] = updated_record[field]

    save_subscriptions(df)


def delete_subscription(subscription_id):
    """Delete one subscription by its ID."""

    df = load_subscriptions()

    if not df["id"].eq(subscription_id).any():
        raise ValueError("Subscription ID was not found.")

    updated_df = df[df["id"] != subscription_id].copy()
    save_subscriptions(updated_df)


def monthly_equivalent(price, billing_cycle):
    """Convert a monthly or annual price into monthly cost."""

    price = float(price)

    if price < 0:
        raise ValueError("Price cannot be negative.")

    if billing_cycle == "Monthly":
        return price

    if billing_cycle == "Annual":
        return price / 12

    raise ValueError("Unknown billing cycle.")


def annual_equivalent(price, billing_cycle):
    """Calculate the annual-equivalent subscription cost."""

    return monthly_equivalent(price, billing_cycle) * 12


if __name__ == "__main__":
    df = load_subscriptions()

    print("SUBSIGHT - Data Manager Test")
    print("----------------------------")
    print(f"Records loaded: {len(df)}")

    if not df.empty:
        first = df.iloc[0]

        monthly = monthly_equivalent(
            first["price"],
            first["billing_cycle"],
        )

        print(f"First subscription: {first['name']}")
        print(f"Monthly-equivalent cost: ₹{monthly:.2f}")
