import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# Load your dataset
df = pd.read_csv('completed_events_large.csv')

# Make a copy to work on
df_cleaned = df.copy()

# Encode the winner column
df_cleaned['winner_encoded'] = df_cleaned['winner'].map({'Red': 1, 'Blue': 0})

# Drop unnecessary and post-fight columns
columns_to_drop = [
    'event_name', 'referee_name', 'method',
    'red_fighter_name', 'blue_fighter_name',  # Keep in reference set only
    'winner',
    'fight_total_strikes_landed', 'fight_total_strikes_attempted',
    'fight_significant_strikes_landed', 'fight_significant_strikes_attempted',
    'fight_takedowns_landed', 'fight_takedowns_attempted',
    'fight_control_time_seconds', 'fight_knockdowns',
    'fight_submission_attempts', 'fight_reversals',
    'red_fight_total_strikes_landed', 'blue_fight_total_strikes_landed',
    'red_fight_significant_strikes_landed', 'blue_fight_significant_strikes_landed',
    'red_fight_takedowns_landed', 'blue_fight_takedowns_landed',
    'red_fight_control_time_seconds', 'blue_fight_control_time_seconds'
]
df_cleaned.drop(columns=columns_to_drop, inplace=True, errors='ignore')

# Fill missing categorical values with 'Unknown'
df_cleaned['red_stance'].fillna('Unknown', inplace=True)
df_cleaned['blue_stance'].fillna('Unknown', inplace=True)

# Get numeric columns (excluding target)
numeric_cols = df_cleaned.select_dtypes(include=['float64', 'int64']).columns.tolist()
numeric_cols.remove('winner_encoded')

# Impute missing values in numeric columns with median
imputer = SimpleImputer(strategy='median')
df_cleaned[numeric_cols] = imputer.fit_transform(df_cleaned[numeric_cols])

# Normalize numeric features
scaler = StandardScaler()
df_cleaned[numeric_cols] = scaler.fit_transform(df_cleaned[numeric_cols])

# One-hot encode categorical stance columns
df_cleaned = pd.get_dummies(df_cleaned, columns=['red_stance', 'blue_stance'], prefix=['red_stance', 'blue_stance'])

# Save final training dataset (only rows with known winner)
train_data = df_cleaned.dropna(subset=['winner_encoded'])
train_data.to_csv('ufc_preprocessed_train_data.csv', index=False)

# Save reference file with fighter names and labels
reference_data = df[['red_fighter_name', 'blue_fighter_name', 'winner']].copy()
reference_data['winner_encoded'] = train_data['winner_encoded'].values
reference_data.to_csv('ufc_reference_data.csv', index=False)

print("✅ Preprocessing complete.")
print("Saved: ufc_preprocessed_train_data.csv and ufc_reference_data.csv")
