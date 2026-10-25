# SUBSIGHT — Smart Subscription Decision Advisor

SUBSIGHT is a Python-based decision-support application that helps users evaluate recurring subscription expenses using Mamdani Fuzzy Logic and a traditional weighted-score baseline.

The application compares both decision-making methods and recommends whether a subscription should be kept, reviewed, downgraded, or cancelled.

## Features

- **Subscription Management:** Add, edit, and delete subscription records.
- **Interactive Dashboard:** Review subscription expenditure and potential savings.
- **Fuzzy Logic Recommendations:** Evaluate subscriptions using membership functions and fuzzy rules.
- **Weighted-Score Baseline:** Compare fuzzy recommendations with a traditional scoring method.
- **What-If Simulator:** Test changes to subscription inputs without modifying saved records.
- **Fuzzy Logic Explorer:** Explore membership functions and test sample inputs.
- **Experiment Results:** Compare both methods across predefined test scenarios.
- **Automated Tests:** Validate scoring, recommendations, and savings calculations.

## Technologies Used

- Python
- Streamlit
- scikit-fuzzy
- NumPy
- Pandas
- Plotly
- Pytest

## Decision-Making Methodology

### 1. Mamdani Fuzzy Logic

The fuzzy inference system evaluates monthly-equivalent cost, usage frequency, importance, cheaper alternatives, and cancellation fees. It applies membership functions and fuzzy rules, then uses centroid defuzzification to calculate a retention suitability score.

### 2. Weighted-Score Baseline

A traditional weighted-score method evaluates the same predefined scenarios independently. The results are compared with those from the fuzzy system.

### Possible Recommendations

- **Keep:** Retain the subscription.
- **Review:** Examine whether the subscription remains useful.
- **Downgrade:** Consider a less expensive plan.
- **Cancel:** Consider cancelling the subscription.

These are decision-support recommendations; the application does not automatically change or cancel subscriptions.

## Project Structure

```text
smart-subscription-advisor/
├── app.py
├── baseline.py
├── data_manager.py
├── fuzzy_engine.py
├── generate_dataset.py
├── savings.py
├── test_decision_system.py
├── requirements.txt
├── requirements-lock.txt
├── data/
│   ├── subscriptions.csv
│   └── test_scenarios.csv
└── .gitignore
```

## Installation and Execution

### Prerequisites

Install Python 3.11 or a compatible version supported by the project's dependencies.

### 1. Clone the repository

```bash
git clone https://github.com/bhavyammehta/smart-subscription-advisor.git
cd smart-subscription-advisor
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the application

```bash
python -m streamlit run app.py
```

Open the local URL displayed in the terminal.

## Testing

Run the automated test suite:

```bash
python -m pytest test_decision_system.py -v
```

The recorded test run passed all 20 tests. Four deprecation warnings were also reported by the fuzzy-logic dependency.

## Experimental Results

The project was evaluated using 20 predefined test scenarios.

| Evaluation measure | Recorded result |
|---|---:|
| Fuzzy method agreement with expected actions | 16/20 (80%) |
| Baseline agreement with expected actions | 15/20 (75%) |
| Agreement between both methods | 85% |
| Automated tests passed | 20/20 |

These results measure agreement with predefined design expectations, not real-world predictive accuracy. The sample subscription data is fictional.

## Limitations

- Membership functions, rules, weights, and thresholds are initial design choices.
- The predefined dataset does not represent real customer behaviour.
- Savings estimates depend on assumptions and may differ from actual savings.
- Local CSV storage may not persist changes across some hosted redeployments.
- Recommendations require further evaluation before practical financial use.

## Academic Context

**Project:** Smart Subscription Decision Advisor Using Fuzzy Logic  
**Application:** SUBSIGHT  
**Course:** Soft Computing  
**Program:** B.Tech CSE (AI/ML)  
**University:** Adani University

## License

No open-source license has been specified yet. All rights and reuse permissions remain subject to the repository owner's terms until a license is added.
