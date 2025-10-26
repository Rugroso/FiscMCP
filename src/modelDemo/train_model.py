from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import pandas as pd
import joblib

df = pd.read_csv('business_growth_dataset.csv')

# Normalize 'formalization_level' column
df = df.drop('sector', axis=1)
df = df.drop('business_id', axis=1)
df = df.drop('sales_growth_last_6m', axis=1)
df = df.drop('formalization_level', axis=1)
# formalization_map = {
#     'Informal': 0,
#     'Formal': 1
# }
# df['formalization_level'] = df['formalization_level'].map(formalization_map)
credit_availabe = {
    'No': 0,
    'Si': 1,
}
df['access_to_credit'] = df['access_to_credit'].map(credit_availabe)

# If you want to consider 3 possible inputs for 'formalization_level', ensure only these values exist
# df = df[df['formalization_level'].isin([0, 1, 2])]
# Sample data
X = df.drop('growth_potential', axis=1)  # Features
y = df['growth_potential']               # Target variable

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train the RandomForestRegressor
regressor = RandomForestRegressor(n_estimators=100, random_state=42)
regressor.fit(X_train, y_train)

# Save the trained model to a file
joblib.dump(regressor, 'business_growth_predictor.pkl')
# Make predictions
y_pred = regressor.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse}")