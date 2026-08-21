"""
ML Module for Real-Time Ransomware Detection.

This module provides behavioral pattern classification to distinguish
normal system activity from ransomware-like behavior based on
system telemetry features extracted from monitored events.

Module Responsibilities:
    - Preprocessing behavioral features for ML inference
    - Training and evaluating classification models
    - Real-time inference producing structured ML signals
    - Feature contract validation

This module does NOT:
    - Monitor files, processes, or network activity
    - Make final risk severity decisions
    - Take protective actions (kill, block, quarantine)
    - Replace the Central Risk Engine

Architecture Position:
    Feature Extractor → ML Preprocessing → ML Model → ML Result → Central Risk Engine
"""

__version__ = "0.1.0"
