import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix
)
from xgboost import XGBClassifier
import matplotlib.pyplot as plt
import seaborn as sns

columns = [
    "duration","protocol_type","service","flag","src_bytes","dst_bytes",
    "land","wrong_fragment","urgent","hot","num_failed_logins","logged_in",
    "num_compromised","root_shell","su_attempted","num_root","num_file_creations",
    "num_shells","num_access_files","num_outbound_cmds","is_host_login",
    "is_guest_login","count","srv_count","serror_rate","srv_serror_rate",
    "rerror_rate","srv_rerror_rate","same_srv_rate","diff_srv_rate",
    "srv_diff_host_rate","dst_host_count","dst_host_srv_count",
    "dst_host_same_srv_rate","dst_host_diff_srv_rate","dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate","dst_host_serror_rate","dst_host_srv_serror_rate",
    "dst_host_rerror_rate","dst_host_srv_rerror_rate","label","difficulty"
]

drop_cols = [
    "difficulty",
    "srv_serror_rate", "dst_host_srv_serror_rate",
    "srv_rerror_rate", "dst_host_srv_rerror_rate",
]
categorical_cols = ["protocol_type", "service", "flag"]

# ============================================================
# ATTACK FAMILY MAPPING
# ============================================================
# NSL-KDD's 22+ attack types belong to four well-established families.
# We map each specific attack to its family, then treat normal as its
# own class. Result: 5 classes total.
#
# DoS  — volumetric attacks that overwhelm a service
# Probe — scanning/reconnaissance to find vulnerabilities
# R2L  — Remote to Local: attacker on the internet tries to gain
#         local access to a machine they have no account on
# U2R  — User to Root: attacker with a local account tries to
#         escalate to root/admin privileges
#
# This mapping is standard in IDS literature and matches the original
# KDD Cup 1999 categorization.

family_map = {
    # DoS
    "neptune": "DoS", "smurf": "DoS", "pod": "DoS", "teardrop": "DoS",
    "land": "DoS", "back": "DoS", "apache2": "DoS", "udpstorm": "DoS",
    "processtable": "DoS", "mailbomb": "DoS",
    # Probe
    "ipsweep": "Probe", "portsweep": "Probe", "satan": "Probe",
    "nmap": "Probe", "mscan": "Probe", "saint": "Probe",
    # R2L
    "guess_passwd": "R2L", "ftp_write": "R2L", "imap": "R2L",
    "warezmaster": "R2L", "spy": "R2L", "phf": "R2L", "multihop": "R2L",
    "warezclient": "R2L", "sendmail": "R2L", "named": "R2L",
    "snmpgetattack": "R2L", "snmpguess": "R2L", "httptunnel": "R2L",
    "xlock": "R2L", "xsnoop": "R2L", "worm": "R2L",
    # U2R
    "buffer_overflow": "U2R", "loadmodule": "U2R", "rootkit": "U2R",
    "perl": "U2R", "sqlattack": "U2R", "xterm": "U2R", "ps": "U2R",
}

def map_family(label):
    if label == "normal":
        return "normal"
    return family_map.get(label, "other")

# ============================================================
# LOAD + PREP
# ============================================================
train_df = pd.read_csv("../data/KDDTrain.txt", names=columns)
test_df  = pd.read_csv("../data/KDDTest.txt",  names=columns)

# keep raw labels for the within-family analysis later
train_raw_labels = train_df["label"].copy()
test_raw_labels  = test_df["label"].copy()

# map to families
train_df["family"] = train_df["label"].apply(map_family)
test_df["family"]  = test_df["label"].apply(map_family)

train_df = train_df.drop(columns=drop_cols + ["label"])
test_df  = test_df.drop(columns=drop_cols  + ["label"])

for col in categorical_cols:
    le = LabelEncoder()
    combined = pd.concat([train_df[col], test_df[col]], axis=0)
    le.fit(combined)
    train_df[col] = le.transform(train_df[col])
    test_df[col]  = le.transform(test_df[col])

X_train = train_df.drop(columns=["family"])
X_test  = test_df.drop(columns=["family"])
y_train_raw = train_df["family"]
y_test_raw  = test_df["family"]

# ============================================================
# ENCODE FAMILY LABELS TO INTEGERS
# ============================================================
# XGBoost needs integer targets for multiclass.
# LabelEncoder on the family column: DoS=0, Probe=1, R2L=2, U2R=3, normal=4
# (alphabetical order, exact mapping printed below)
family_encoder = LabelEncoder()
family_encoder.fit(pd.concat([y_train_raw, y_test_raw]))
y_train = family_encoder.transform(y_train_raw)
y_test  = family_encoder.transform(y_test_raw)

print("Family encoding:")
for i, cls in enumerate(family_encoder.classes_):
    count_train = (y_train_raw == cls).sum()
    count_test  = (y_test_raw  == cls).sum()
    print(f"  {i}: {cls:<8} train={count_train:6d}  test={count_test:6d}")

# ============================================================
# CLASS WEIGHTS FOR MULTICLASS
# ============================================================
# scale_pos_weight only works for binary XGBoost.
# For multiclass, we use sample_weight in .fit() instead.
# We compute per-sample weights inversely proportional to class frequency:
# rare classes (U2R, R2L) get higher weight so the model pays more
# attention to them during training.
#
# formula per sample: total_samples / (n_classes * class_count)
# this is the standard balanced class weight formula from sklearn.
n_classes = len(family_encoder.classes_)
class_counts = pd.Series(y_train).value_counts().sort_index()
class_weights = len(y_train) / (n_classes * class_counts)

# map each training sample to its class weight
sample_weights = np.array([class_weights[y] for y in y_train])

print("\nClass weights (higher = rarer class gets more attention):")
for i, cls in enumerate(family_encoder.classes_):
    print(f"  {cls:<8}: {class_weights[i]:.4f}")

# ============================================================
# MULTICLASS XGBOOST
# ============================================================
# objective="multi:softmax" tells XGBoost this is a multiclass problem.
# num_class must match the number of unique labels.
# Everything else stays the same as the binary model.
# We do NOT use scale_pos_weight here — that's binary only.
# Class imbalance is handled via sample_weight in .fit() instead.
model = XGBClassifier(
    objective="multi:softmax",
    num_class=n_classes,
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    eval_metric="mlogloss",
    n_jobs=-1
)

model.fit(X_train, y_train, sample_weight=sample_weights)
y_pred = model.predict(X_test)

# decode back to family names for readable output
y_test_names = family_encoder.inverse_transform(y_test)
y_pred_names = family_encoder.inverse_transform(y_pred)

print("\n=== MULTICLASS RESULTS ON KDDTest+ ===")
print(f"Overall Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print()
print(classification_report(y_test_names, y_pred_names))

# ============================================================
# CONFUSION MATRIX
# ============================================================
# For multiclass, the confusion matrix is 5x5 instead of 2x2.
# Each row = actual class, each column = predicted class.
# Diagonal = correct predictions.
# Off-diagonal = what the model confused each class with.
# Particularly interesting: what does R2L get confused with?
# (Normal? That would confirm the camouflage finding from binary.)
class_names = family_encoder.classes_
cm = confusion_matrix(y_test_names, y_pred_names, labels=class_names)

plt.figure(figsize=(8, 6))
sns.heatmap(
    cm, annot=True, fmt="d", cmap="Blues",
    xticklabels=class_names, yticklabels=class_names
)
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Confusion Matrix — 5-Class (KDDTest+)")
plt.tight_layout()
plt.savefig("mc_01_confusion_matrix.png", dpi=120, bbox_inches="tight")
plt.close()
print("Saved confusion matrix.")

# ============================================================
# WITHIN-FAMILY ANALYSIS: which specific attacks are being missed
# ============================================================
# For each family, break down recall by specific attack type.
# This shows which attacks drag each family's recall down.
# Connects back to the binary analysis — are the same attacks
# being missed, or does the multiclass model change what's hard?

analysis = pd.DataFrame({
    "true_family":   y_test_names,
    "pred_family":   y_pred_names,
    "true_label":    test_raw_labels.values,
}, index=X_test.index)

analysis["correct"] = (analysis["true_family"] == analysis["pred_family"]).astype(int)

print("\n=== WITHIN-FAMILY BREAKDOWN ===")
for family in sorted(set(family_map.values())):
    family_rows = analysis[analysis["true_family"] == family]
    if len(family_rows) == 0:
        continue

    family_recall = family_rows["correct"].mean()
    print(f"\n{family} (overall recall: {family_recall:.3f})")

    # per-attack breakdown within this family
    per_attack = (
        family_rows.groupby("true_label")
        .agg(total=("correct","count"), caught=("correct","sum"))
        .assign(recall=lambda df: df["caught"]/df["total"])
        .sort_values("recall", ascending=True)
    )
    print(per_attack.to_string())

# ============================================================
# VISUAL: per-family recall bar chart
# ============================================================
family_recalls = {}
for family in class_names:
    if family == "normal":
        continue
    rows = analysis[analysis["true_family"] == family]
    family_recalls[family] = rows["correct"].mean() if len(rows) > 0 else 0

plt.figure(figsize=(7, 4))
plt.bar(family_recalls.keys(), family_recalls.values(),
        color=["steelblue","darkorange","forestgreen","crimson"])
plt.ylim(0, 1.05)
plt.ylabel("Recall")
plt.title("Per-Family Recall — Multiclass Model (KDDTest+)")
plt.tight_layout()
plt.savefig("mc_02_family_recall.png", dpi=120, bbox_inches="tight")
plt.close()
print("\nSaved family recall chart.")
