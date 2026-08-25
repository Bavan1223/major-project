# ML Dataset Research — Ransomware Behavioral Detection

## Current Model Status

- **Model**: Random Forest Classifier (scikit-learn)
- **Training data**: 120 samples (synthetic behavioral scenarios)
- **Features**: 10 behavioral features (file operations, process/network counts)
- **Live detection accuracy**: 0.9934 probability on safe simulation
- **Status**: Working for lab demonstration

## Recommended Datasets for Future Improvement

### 1. MLRan (Primary Recommendation)
- **Repository**: [faithfulco/mlran](https://github.com/faithfulco/mlran)
- **Description**: Large-scale behavioral ransomware dataset with 4,800+ dynamically analyzed samples spanning 64 ransomware families
- **Covers**: Locker, crypto, RaaS, and modern ransomware types (2006-2024)
- **Why useful**: Behavioral features from dynamic analysis — directly compatible with our feature extraction approach

### 2. RanSMAP
- **Repository**: [manabu-hirano/RanSMAP](https://github.com/manabu-hirano/RanSMAP)
- **Description**: Storage and memory access patterns of ransomware vs benign apps
- **Why useful**: Lower-level behavioral signals (I/O patterns, memory access)

### 3. RansomSet
- **Repository**: [gabrielolivs/RansomSet](https://github.com/gabrielolivs/RansomSet)
- **Description**: Features from WannaCry, Ryuk, CryptoLocker, Conti, Sodinokibi, LockBit analyzed via Cuckoo sandbox
- **Why useful**: Real ransomware families with behavioral features extracted

### 4. MalbehavD-V1
- **Repository**: [mpasco/MalbehavD-V1](https://github.com/mpasco/MalbehavD-V1)
- **Description**: Behavioral characteristics of malware including ransomware, worms, viruses, spyware
- **Why useful**: Multi-class malware classification dataset, ready for ML

### 5. RanSAP
- **Repository**: [manabu-hirano/RanSAP](https://github.com/manabu-hirano/RanSAP)
- **Description**: Storage access patterns of 7 ransomware + 5 benign + 21 variants
- **Why useful**: File I/O behavioral patterns for training

## Feature Mapping

Our current live features:
```
total_events, file_created, file_modified, file_deleted, file_renamed,
unique_files_modified, process_events, network_events,
established_connections, unique_remote_ips
```

These map to behavioral features available in MLRan and RansomSet datasets.

## Improvement Path

1. Download MLRan dataset (CSV with behavioral features)
2. Map MLRan features to our 10-feature vector
3. Retrain Random Forest with 4,800+ samples instead of 120
4. Evaluate with cross-validation (precision, recall, F1)
5. Deploy updated model to `ml/models/ransomware_model.pkl`
6. Validate with safe_simulator.py end-to-end

## Current Limitations (Honest)

- Current 120-sample training set is synthetic (scenario-generated)
- Model works well for our specific simulation pattern
- Real-world generalization is untested
- No offline evaluation with real ransomware behavioral data
- Dataset metrics ≠ live system metrics (clearly documented)

## For Viva

The model demonstrates the CONCEPT of ML-based behavioral ransomware detection.
The architecture supports upgrading to larger datasets without code changes.
The 0.99+ probability on simulation shows the pipeline works end-to-end.
Production deployment would require training on datasets like MLRan (4,800+ samples).
