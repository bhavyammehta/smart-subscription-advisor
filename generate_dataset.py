
from pathlib import Path
import pandas as pd

# Project directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Fictional sample subscription records
subscriptions = [
    ["S001", "Netflix", "Entertainment", "Monthly", 649, 12, 8, 7, 0],
    ["S002", "Spotify", "Music", "Monthly", 119, 25, 8, 5, 0],
    ["S003", "Cloud Storage", "Technology", "Monthly", 499, 8, 6, 7, 0],
    ["S004", "Gym Membership", "Fitness", "Monthly", 1500, 5, 7, 8, 200],
    ["S005", "Online Course", "Education", "Annual", 2400, 2, 5, 8, 0],
    ["S006", "Design Software", "Technology", "Monthly", 1800, 20, 9, 4, 500],
    ["S007", "Gaming Service", "Entertainment", "Monthly", 799, 3, 3, 8, 100],
    ["S008", "News Subscription", "Education", "Annual", 1200, 10, 6, 5, 0],
    ["S009", "Music Premium", "Music", "Monthly", 99, 28, 9, 2, 0],
    ["S010", "Backup Service", "Technology", "Annual", 1800, 15, 8, 4, 100],
    ["S011", "Language App", "Education", "Monthly", 399, 1, 3, 9, 0],
    ["S012", "Video Platform", "Entertainment", "Monthly", 299, 18, 7, 6, 0],
    ["S013", "Premium Fitness", "Fitness", "Annual", 6000, 20, 8, 5, 300],
    ["S014", "Stock Photo Tool", "Technology", "Monthly", 1200, 0, 2, 9, 100],
    ["S015", "Meditation App", "Health", "Monthly", 199, 4, 5, 7, 0],
    ["S016", "Cloud Backup", "Technology", "Monthly", 99, 0, 2, 8, 0],
    ["S017", "Learning Platform", "Education", "Annual", 3600, 25, 10, 3, 0],
    ["S018", "Sports Streaming", "Entertainment", "Monthly", 599, 6, 5, 8, 250],
    ["S019", "Password Manager", "Technology", "Annual", 999, 30, 10, 2, 0],
    ["S020", "Recipe Platform", "Lifestyle", "Monthly", 149, 2, 3, 8, 0],
]

columns = [
    "id", "name", "category", "billing_cycle", "price",
    "usage_days", "importance", "alternatives", "cancellation_fee"
]

subscription_df = pd.DataFrame(subscriptions, columns=columns)

# Create predefined test scenarios.
# Expected actions are design expectations, not measured results.
test_scenarios = [
    ["T001", 100, 28, 9, 2, 0, "Keep"],
    ["T002", 1800, 1, 2, 9, 0, "Cancel"],
    ["T003", 1200, 3, 3, 8, 0, "Cancel"],
    ["T004", 150, 15, 6, 5, 0, "Review"],
    ["T005", 1800, 25, 10, 2, 0, "Keep"],
    ["T006", 900, 10, 5, 8, 100, "Review"],
    ["T007", 500, 2, 2, 9, 0, "Cancel"],
    ["T008", 200, 25, 8, 3, 0, "Keep"],
    ["T009", 1000, 8, 5, 6, 200, "Review"],
    ["T010", 300, 10, 5, 5, 0, "Review"],
    ["T011", 2000, 30, 10, 0, 0, "Keep"],
    ["T012", 50, 0, 1, 10, 0, "Cancel"],
    ["T013", 800, 15, 7, 4, 0, "Review"],
    ["T014", 1600, 4, 4, 8, 900, "Downgrade"],
    ["T015", 400, 20, 8, 3, 0, "Keep"],
    ["T016", 0, 0, 0, 10, 0, "Cancel"],
    ["T017", 2000, 0, 1, 10, 1000, "Cancel"],
    ["T018", 600, 12, 6, 5, 100, "Review"],
    ["T019", 100, 5, 8, 1, 0, "Review"],
    ["T020", 1000, 20, 9, 2, 0, "Keep"],
]

test_columns = [
    "scenario_id", "monthly_cost", "usage_days", "importance",
    "alternatives", "cancellation_fee", "expected_action"
]

test_df = pd.DataFrame(test_scenarios, columns=test_columns)

# Save both datasets
subscription_df.to_csv(
    DATA_DIR / "subscriptions.csv", index=False
)

test_df.to_csv(
    DATA_DIR / "test_scenarios.csv", index=False
)

print("Sample datasets generated successfully.")
print(f"Subscriptions: {len(subscription_df)}")
print(f"Test scenarios: {len(test_df)}")
print(f"Output directory: {DATA_DIR}")
print("\nSample subscriptions:")
print(subscription_df.head())
