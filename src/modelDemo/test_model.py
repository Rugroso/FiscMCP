# test_model.py
import joblib
import pandas as pd

# Load trained model
model = joblib.load("business_growth_predictor.pkl")

# Define mappings (same as training)
formalization_map = {'Informal': 0, 'Formal': 1}
credit_available = {'No': 0, 'Si': 1}

# Example custom input (fill in with realistic values)
custom_input = {
    'business_id': 101, #esta no
    'monthly_income': 12000,
    'monthly_expenses': 4000,
    'net_profit': 10000,
    'profit_margin': 0.25,
    'cash_flow': 20000,
    'debt_ratio': 0.2,
    'business_age_years': 20,
    'employees': 3,
    'sales_growth_last_6m': 0.90, #esta no
    'digitalization_score': 0.5,
    'formalization_level': formalization_map['Formal'], #esta no
    'sector': 'Retail',  # esta tampoco
    'access_to_credit': credit_available['Si'],
    'growth_potential': 0  #esta no
}

# Remove columns not used in training
input_df = pd.DataFrame([custom_input]).drop(['sector', 'growth_potential', 'business_id', 'sales_growth_last_6m', 'formalization_level'], axis=1)

# Predict growth potential
predicted_growth = model.predict(input_df)[0]

print("=== Business Growth Prediction ===")
print(f"Predicted Growth Potential: {predicted_growth:.2f}")
