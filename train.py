import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import matplotlib.pyplot as plt



#load data
df = pd.read_csv('ufc_preprocessed_train_data.csv')


# Fix: One-hot encode remaining object-type columns
categorical_cols = df.select_dtypes(include='object').columns.tolist()
df = pd.get_dummies(df, columns=categorical_cols)


# Add engineered matchup features
df['reach_advantage'] = df['red_reach_cm'] - df['blue_reach_cm']
df['strike_accuracy_diff'] = df['red_significant_strike_accuracy'] - df['blue_significant_strike_accuracy']
df['takedown_accuracy_diff'] = df['red_takedown_accuracy'] - df['blue_takedown_accuracy']
df['defense_diff'] = df['red_significant_strike_defense'] - df['blue_significant_strike_defense']


#split features and target
x = df.drop(columns=['winner_encoded'])
y = df['winner_encoded']

#Split into training and test sets
x_train, x_test, y_train, y_test = train_test_split(x,y, test_size=0.2, random_state=42 , stratify= y)



#train XGBoost Classifier
model = xgb.XGBClassifier(
    n_estimators=200,
    learning_rate=0.2,
    max_depth=5,
    eval_metric='logloss',
    random_state=42
)

model.fit(x_train, y_train)


#prediction
y_pred = model.predict(x_test)

# Evaluate
print("\n Model Evaluation:")
print("Accuracy:", accuracy_score(y_test, y_pred))
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))



# Save the model
joblib.dump(model, 'fight_model.pkl')
print("\nSaved trained model as fight_model.pkl")


# # Feature Importance Plot
# plt.figure(figsize=(14, 6))
# xgb.plot_importance(model, max_num_features=15)
# plt.title("Top 15 Most Important Features")
# plt.tight_layout()
# plt.show()