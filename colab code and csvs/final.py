# -*- coding: utf-8 -*-
"""final_clean.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1qJoAL8188JzX-i3vpJ6su_XKpZpqYVdM
"""

#!pip uninstall scikit-learn --yes
#!pip uninstall imblearn --yes
#!pip install scikit-learn==1.2.2
#!pip install imblearn

#models
import xgboost as xgb
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

#utilities
import numpy as np
import pandas as pd
import joblib
#from joblib import dump

#pre-processing
from imblearn.over_sampling import SMOTE
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_predict, StratifiedKFold

#visualization
import matplotlib.pyplot as plt
import seaborn as sns

#evaluation
from sklearn.metrics import roc_curve, auc, precision_recall_curve, f1_score, precision_score, recall_score, confusion_matrix, classification_report

"""loading csv:"""

df = pd.read_csv('final.csv') #down scaled big dataset
test2 = pd.read_csv('final_external_test.csv') #dikie benigns and virusshare malwares combined (2k total)

df

plt.figure(figsize=(12,10))
cor = np.abs(df.corr()) #absolute, doesnt matter if its negative or positive correlation
sns.heatmap(cor, annot=True,cmap=plt.cm.Reds, vmin=0, vmax=1)
plt.show()

t = df['malware']
X = df.drop('malware', axis=1)

t_test = test2['malware']
X_test = test2.drop(columns=['malware'])

X_train = X
t_train = t


#X_train, X_test, t_train, t_test = train_test_split(X, t, test_size=0.3, random_state=42) #uncomment to test against validation (will overwite the groups that fit for external test)

# Apply resampling only on the training data
smote = SMOTE(random_state=42)
#X_train, t_train = smote.fit_resample(X_train, t_train) #uncomment if using validation (and uncomment the train_test_split from cell above)

# Initialize the StandardScaler
print(X_train.iloc[0])
X_train = X_train.values
X_test = X_test.values
standard_scaler = StandardScaler()
print(X_train[0])
# Fit the scaler on the training data (X_train) and then transform it
X_train = standard_scaler.fit_transform(X_train)

# Transform the test data (X_test) using the same scaler that was fit on the train
X_test = standard_scaler.transform(X_test)

clf = RandomForestClassifier(n_estimators=100, random_state=0)
clf.fit(X_train, t_train)

# Save the model to disk
joblib.dump(clf, 'random_forest_model.joblib')

#save scaler to disk
joblib.dump(standard_scaler, 'scaler.joblib')

from sklearn.model_selection import cross_val_predict, StratifiedKFold


# Initialize classifiers
classifiers = {
    "Decision Tree": DecisionTreeClassifier(random_state=0),
    "XGBoost": xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=0),
    "KNN": KNeighborsClassifier(n_neighbors=5),
    "Logistic Regression": LogisticRegression(random_state=0),
    "SVM": SVC(random_state=0, probability=True)  # Ensure probability is True for ROC curves
}

# Setting up 5-fold stratified cross-validation
cv = StratifiedKFold(n_splits=5)

# Function to plot ROC and Precision-Recall curves
def plot_curves(fpr, tpr, model_name, roc_auc, precision, recall):
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC - {model_name}')
    plt.legend(loc="lower right")

    plt.subplot(1, 2, 2)
    plt.plot(recall, precision, color='blue', lw=2, label='Precision-Recall curve')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(f'Precision-Recall - {model_name}')
    plt.legend(loc="lower left")
    plt.show()

# Evaluate each classifier
for name, clf in classifiers.items():
    t_pred_prob = cross_val_predict(clf, X, t, cv=cv, method='predict_proba')[:, 1]
    t_pred = cross_val_predict(clf, X, t, cv=cv, method='predict')

    fpr, tpr, _ = roc_curve(t, t_pred_prob)
    roc_auc = auc(fpr, tpr)
    precision, recall, _ = precision_recall_curve(t, t_pred_prob)

    plot_curves(fpr, tpr, name, roc_auc, precision, recall)

    cm = confusion_matrix(t, t_pred)
    sensitivity = recall_score(t, t_pred)  # Recall is the same as sensitivity
    specificity = cm[0, 0] / (cm[0, 0] + cm[0, 1])  # Specificity calculation
    fpr_metric = 1 - specificity  # Calculating False Positive Rate

    print(f"{name} - Confusion Matrix:\n{cm}\n")
    print(f"{name} - Precision: {precision_score(t, t_pred):.2f}, Recall (Sensitivity): {sensitivity:.2f}, F1 Score: {f1_score(t, t_pred):.2f}\n")
    print(f"{name} - Sensitivity: {sensitivity:.2f}, Specificity: {specificity:.2f}, FPR: {fpr_metric:.2f}\n")

# Initialize classifiers
classifiers = {
    "Decision Tree": DecisionTreeClassifier(random_state=0),
    "XGBoost": xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=0),
    "KNN": KNeighborsClassifier(n_neighbors=5),
    "Logistic Regression": LogisticRegression(random_state=0),
     "SVM": SVC(random_state=0)
}

# Function to plot ROC and Precision-Recall curves
def plot_curves(fpr, tpr, model_name, roc_auc, precision, recall):
    # ROC Curve
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'ROC - {model_name}')
    plt.legend(loc="lower right")

    # Precision-Recall Curve
    plt.subplot(1, 2, 2)
    plt.plot(recall, precision, color='blue', lw=2, label='Precision-Recall curve')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(f'Precision-Recall - {model_name}')
    plt.legend(loc="lower left")
    plt.show()

# Loop through classifiers to train, predict, and plot curves
for name, clf in classifiers.items():
    clf.fit(X_train, t_train)
    t_pred = clf.predict(X_test)
    t_pred_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else clf.decision_function(X_test)

    fpr, tpr, _ = roc_curve(t_test, t_pred_prob)
    roc_auc = auc(fpr, tpr)
    plot_curves(fpr, tpr, name, roc_auc, *precision_recall_curve(t_test, t_pred_prob)[:2])

    # Confusion Matrix
    cm = confusion_matrix(t_test, t_pred)
    print(f"{name} - Confusion Matrix:\n{cm}\n")

    # Precision, Recall, F1 Score
    precision = precision_score(t_test, t_pred)
    recall = recall_score(t_test, t_pred)
    f1 = f1_score(t_test, t_pred)
    print(f"{name} - Precision: {precision:.2f}, Recall: {recall:.2f}, F1 Score: {f1:.2f}\n")

    # Sensitivity and Specificity
    sensitivity = recall  # Recall is the same as sensitivity
    specificity = cm[0, 0] / (cm[0, 0] + cm[0, 1])
    fpr_metric = 1 - specificity  # Calculating False Positive Rate
    print(f"{name} - Sensitivity: {sensitivity:.2f}, Specificity: {specificity:.2f}, FPR: {fpr_metric:.2f}\n")

classifiers = {
    "Decision Tree": DecisionTreeClassifier(random_state=0),
    "XGBoost": xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=0),
    "KNN": KNeighborsClassifier(n_neighbors=10),
    "Logistic Regression": LogisticRegression(random_state=0),
}

# Creating the ensemble classifier with soft voting
voting_clf = VotingClassifier(estimators=[(name, clf) for name, clf in classifiers.items()], voting='soft')

# Fit the ensemble classifier
voting_clf.fit(X_train, t_train)

# Predict probabilities and classes
voting_pred_prob = voting_clf.predict_proba(X_test)[:, 1]
voting_pred = voting_clf.predict(X_test)

# Compute metrics and plot ROC curve
fpr, tpr, _ = roc_curve(t_test, voting_pred_prob)
roc_auc = auc(fpr, tpr)
plot_curves(fpr, tpr, "Voting Ensemble", roc_auc, *precision_recall_curve(t_test, voting_pred_prob)[:2])

# Confusion Matrix and classification report
print(f"Voting Ensemble - Confusion Matrix:\n{confusion_matrix(t_test, voting_pred)}\n")
print(f"Voting Ensemble - Classification Report:\n{classification_report(t_test, voting_pred)}\n")