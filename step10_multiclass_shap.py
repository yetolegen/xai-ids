import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
import shap
import matplotlib.pyplot as plt

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

family_map = {
    "neptune": "DoS", "smurf": "DoS", "pod": "DoS", "teardrop": "DoS",
    "land": "DoS", "back": "DoS", "apache2": "DoS", "udpstorm": "DoS",
    "processtable": "DoS", "mailbomb": "DoS",
    "ipsweep": "Probe", "portsweep": "Probe", "satan": "Probe",
    "nmap": "Probe", "mscan": "Probe", "saint": "Probe",
    "guess_passwd": "R2L", "ftp_write": "R2L", "imap": "R2L",
    "warezmaster": "R2L", "spy": "R2L", "phf": "R2L", "multihop": "R2L",
    "warezclient": "R2L", "sendmail": "R2L", "named": "R2L",
    "snmpgetattack": "R2L", "snmpguess": "R2L", "httptunnel": "R2L",
    "xlock": "R2L", "xsnoop": "R2L", "worm": "R2L",
    "buffer_overflow": "U2R", "loadmodule": "U2R", "rootkit": "U2R",
    "perl": "U2R", "sqlattack": "U2R", "xterm": "U2R", "ps": "U2R",
}

def map_family(label):
    if label == "normal":
        return "normal"
    return family_map.get(label, "other")

# ============================================================
# LOAD + PREP (same as step 9)
# ============================================================
train_df = pd.read_csv("../data/KDDTrain.txt", names=columns)
test_df  = pd.read_csv("../data/KDDTest.txt",  names=columns)

test_raw_labels = test_df["label"].copy()

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

family_encoder = LabelEncoder()
family_encoder.fit(pd.concat([y_train_raw, y_test_raw]))
y_train = family_encoder.transform(y_train_raw)
y_test  = family_encoder.transform(y_test_raw)

n_classes    = len(family_encoder.classes_)
class_counts = pd.Series(y_train).value_counts().sort_index()
class_weights = len(y_train) / (n_classes * class_counts)
sample_weights = np.array([class_weights[y] for y in y_train])

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

# ============================================================
# MULTICLASS SHAP
# ============================================================
# For multiclass XGBoost, TreeExplainer returns a LIST of SHAP arrays
# rather than a single array. There's one array per class:
# shap_values[0] = SHAP values pushing toward class 0 (DoS)
# shap_values[1] = SHAP values pushing toward class 1 (Probe)
# shap_values[2] = SHAP values pushing toward class 2 (R2L)
# shap_values[3] = SHAP values pushing toward class 3 (U2R)
# shap_values[4] = SHAP values pushing toward class 4 (normal)
#
# Each array has shape (n_samples, n_features).
# A positive SHAP value in shap_values[0] for a given feature means
# that feature pushed the prediction toward DoS for that sample.
# This is fundamentally different from binary where there's one array.
explainer = shap.TreeExplainer(model)

# stratified sample: 200 per family (except U2R which is tiny, take all)
# we sample per family so each class has equal representation in SHAP plots
sample_indices = []
for family in family_encoder.classes_:
    idx = X_test[y_test_raw == family].index
    n   = min(200, len(idx))
    sample_indices.extend(idx[:n].tolist())

X_sample      = X_test.loc[sample_indices]
y_sample_raw  = y_test_raw.loc[sample_indices]

print(f"Sample sizes per family:")
for fam in family_encoder.classes_:
    print(f"  {fam}: {(y_sample_raw==fam).sum()}")

# compute SHAP — older shap returns a list of 5 arrays (one per class),
# newer shap returns a single (n_samples, n_features, n_classes) array.
# Normalize to a list of per-class arrays either way.
shap_values_raw = explainer.shap_values(X_sample)
if isinstance(shap_values_raw, list):
    shap_values_list = shap_values_raw
else:
    shap_values_list = [shap_values_raw[:, :, i] for i in range(shap_values_raw.shape[2])]
print(f"\nshap_values_list length: {len(shap_values_list)} (one per class)")
print(f"Each array shape: {shap_values_list[0].shape}")

# ============================================================
# PLOT 1: GLOBAL BEESWARM PER CLASS
# ============================================================
# For each of the 5 classes, plot a beeswarm showing which features
# most strongly push the model toward predicting THAT class.
# This directly answers: "what makes the model say DoS vs Probe vs R2L?"
# Comparing across plots shows whether families have distinct signatures.

for i, family in enumerate(family_encoder.classes_):
    plt.figure()
    shap.summary_plot(
        shap_values_list[i],  # SHAP values for class i only
        X_sample,
        show=False,
        max_display=15,
        plot_size=(10, 7)
    )
    plt.title(f"SHAP — Features pushing toward '{family}' prediction")
    plt.tight_layout()
    plt.savefig(f"mc_shap_{family}.png", dpi=120, bbox_inches="tight")
    plt.close()
    print(f"Saved SHAP beeswarm for {family}")

# ============================================================
# PLOT 2: MEAN SHAP HEATMAP ACROSS ALL FAMILIES
# ============================================================
# A heatmap where:
# - rows = top 15 features (by total importance across all classes)
# - columns = the 5 classes
# - cell value = mean SHAP for that feature pushing toward that class
#
# This is the single most informative multiclass SHAP visualization.
# It shows at a glance which features are unique to each family
# vs which features are shared. A feature that's dark red for DoS
# and near-zero for all others is a DoS-specific signature.
# A feature that's dark for both DoS and Probe but blue for normal
# is a general attack indicator, not family-specific.

# compute mean |SHAP| per feature across all classes to rank importance
mean_abs_all = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values_list], axis=0)
top15_idx    = np.argsort(mean_abs_all)[::-1][:15]
top15_names  = X_train.columns[top15_idx]

# build the heatmap matrix: rows=features, cols=classes
heatmap_data = pd.DataFrame(
    index=top15_names,
    columns=family_encoder.classes_,
    dtype=float
)
for i, family in enumerate(family_encoder.classes_):
    # mean SHAP (not absolute) so direction is preserved
    # positive = this feature pushes toward this class
    # negative = this feature pushes away from this class
    heatmap_data[family] = shap_values_list[i][:, top15_idx].mean(axis=0)

plt.figure(figsize=(10, 8))
sns_ax = plt.gca()
import seaborn as sns
sns.heatmap(
    heatmap_data.astype(float),
    cmap="coolwarm",
    center=0,
    annot=True,
    fmt=".2f",
    ax=sns_ax,
    linewidths=0.5
)
plt.title("Mean SHAP per Feature per Family\n"
          "(red = pushes toward this class, blue = pushes away)")
plt.xlabel("Attack Family")
plt.ylabel("Feature")
plt.tight_layout()
plt.savefig("mc_shap_heatmap.png", dpi=120, bbox_inches="tight")
plt.close()
print("Saved SHAP heatmap across families.")

# ============================================================
# PLOT 3: WATERFALL FOR ONE REPRESENTATIVE PER FAMILY
# ============================================================
# Pick one correctly predicted example from each family and
# explain it with a waterfall plot. Shows how the model reasons
# about a specific DoS connection vs a specific Probe connection etc.
# More grounded than the global plots — connects back to individual predictions.

y_pred      = model.predict(X_test)
y_pred_fam  = family_encoder.inverse_transform(y_pred)
y_test_fam  = y_test_raw.values

base_values = explainer.expected_value  # list of base values, one per class

print("\n--- Waterfall plots per family ---")
for i, family in enumerate(family_encoder.classes_):
    # find a correctly predicted example from this family
    correct_mask = (y_test_fam == family) & (y_pred_fam == family)
    correct_idx  = X_test.index[correct_mask]

    if len(correct_idx) == 0:
        print(f"{family}: no correctly predicted examples, skipping")
        continue

    row_idx  = correct_idx[0]
    row      = X_test.loc[[row_idx]]
    sv_raw   = explainer.shap_values(row)  # list of 5 arrays, or (1, 37, 5) array
    sv       = sv_raw if isinstance(sv_raw, list) else [sv_raw[:, :, c] for c in range(sv_raw.shape[2])]

    # sv[i] = SHAP values for class i for this one row, shape (1, 37)
    # sv[i][0] = the actual 37 SHAP values for class i
    explanation = shap.Explanation(
        values=sv[i][0],                    # SHAP values for THIS class
        base_values=base_values[i],         # base value for THIS class
        data=row.iloc[0].values,
        feature_names=list(X_test.columns)
    )

    plt.figure(figsize=(10, 7))
    shap.plots.waterfall(explanation, show=False, max_display=12)
    plt.title(f"Waterfall — {family} (correctly predicted)")
    plt.tight_layout()
    plt.savefig(f"mc_waterfall_{family}.png", dpi=120, bbox_inches="tight")
    plt.close()
    print(f"Saved waterfall for {family}")

print("\nAll multiclass SHAP done.")
