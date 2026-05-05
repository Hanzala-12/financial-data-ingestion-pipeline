"""Synthetic data generation using SMOTE and time series augmentation."""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from sklearn.utils import resample


def add_noise_augmentation(
    features: np.ndarray,
    labels: np.ndarray,
    noise_level: float = 0.01,
    n_augmented: int = 1000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Add Gaussian noise to existing samples to create augmented data.
    
    Args:
        features: Original feature array (n_samples, window_size, n_features)
        labels: Original labels (n_samples,)
        noise_level: Standard deviation of Gaussian noise (relative to feature std)
        n_augmented: Number of augmented samples to generate
    
    Returns:
        Augmented features and labels
    """
    n_samples = len(features)
    
    # Randomly select samples to augment
    indices = np.random.choice(n_samples, size=n_augmented, replace=True)
    
    augmented_features = features[indices].copy()
    augmented_labels = labels[indices].copy()
    
    # Add Gaussian noise
    for i in range(len(augmented_features)):
        noise = np.random.normal(0, noise_level, augmented_features[i].shape)
        augmented_features[i] = augmented_features[i] + noise * np.std(augmented_features[i])
    
    return augmented_features, augmented_labels


def time_warp_augmentation(
    features: np.ndarray,
    labels: np.ndarray,
    n_augmented: int = 500,
    warp_factor: float = 0.2
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply time warping to create augmented samples.
    
    Args:
        features: Original feature array (n_samples, window_size, n_features)
        labels: Original labels (n_samples,)
        n_augmented: Number of augmented samples
        warp_factor: Amount of time warping (0-1)
    
    Returns:
        Augmented features and labels
    """
    n_samples, window_size, n_features = features.shape
    
    # Randomly select samples
    indices = np.random.choice(n_samples, size=n_augmented, replace=True)
    
    augmented_features = []
    augmented_labels = labels[indices].copy()
    
    for idx in indices:
        sample = features[idx].copy()
        
        # Create random time warp
        warp_steps = np.arange(window_size)
        warp_amount = int(window_size * warp_factor)
        
        # Random compression/expansion
        if np.random.rand() > 0.5:
            # Compress
            compressed_steps = np.linspace(0, window_size - 1, window_size - warp_amount)
            warped_sample = np.zeros((window_size, n_features))
            for f in range(n_features):
                warped_sample[:, f] = np.interp(warp_steps, compressed_steps, 
                                                 sample[:len(compressed_steps), f])
        else:
            # Expand
            expanded_steps = np.linspace(0, window_size - 1, window_size + warp_amount)
            warped_sample = np.zeros((window_size, n_features))
            for f in range(n_features):
                expanded_sample = np.interp(expanded_steps, warp_steps, sample[:, f])
                warped_sample[:, f] = expanded_sample[:window_size]
        
        augmented_features.append(warped_sample)
    
    return np.array(augmented_features), augmented_labels


def window_slicing_augmentation(
    features: np.ndarray,
    labels: np.ndarray,
    n_augmented: int = 500,
    slice_ratio: float = 0.9
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create augmented samples by slicing windows and padding.
    
    Args:
        features: Original feature array (n_samples, window_size, n_features)
        labels: Original labels (n_samples,)
        n_augmented: Number of augmented samples
        slice_ratio: Ratio of window to keep (0-1)
    
    Returns:
        Augmented features and labels
    """
    n_samples, window_size, n_features = features.shape
    slice_size = int(window_size * slice_ratio)
    
    # Randomly select samples
    indices = np.random.choice(n_samples, size=n_augmented, replace=True)
    
    augmented_features = []
    augmented_labels = labels[indices].copy()
    
    for idx in indices:
        sample = features[idx].copy()
        
        # Random start position
        start = np.random.randint(0, window_size - slice_size + 1)
        sliced = sample[start:start + slice_size]
        
        # Pad to original size
        pad_before = start
        pad_after = window_size - slice_size - start
        
        padded = np.pad(sliced, ((pad_before, pad_after), (0, 0)), mode='edge')
        augmented_features.append(padded)
    
    return np.array(augmented_features), augmented_labels


def magnitude_scaling_augmentation(
    features: np.ndarray,
    labels: np.ndarray,
    n_augmented: int = 500,
    scale_range: Tuple[float, float] = (0.9, 1.1)
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Scale the magnitude of features randomly.
    
    Args:
        features: Original feature array (n_samples, window_size, n_features)
        labels: Original labels (n_samples,)
        n_augmented: Number of augmented samples
        scale_range: Range of scaling factors (min, max)
    
    Returns:
        Augmented features and labels
    """
    n_samples = len(features)
    
    # Randomly select samples
    indices = np.random.choice(n_samples, size=n_augmented, replace=True)
    
    augmented_features = features[indices].copy()
    augmented_labels = labels[indices].copy()
    
    # Apply random scaling
    for i in range(len(augmented_features)):
        scale = np.random.uniform(scale_range[0], scale_range[1])
        augmented_features[i] = augmented_features[i] * scale
    
    return augmented_features, augmented_labels


def generate_synthetic_data(
    features: np.ndarray,
    labels: np.ndarray,
    target_size: int = 10000,
    methods: Optional[list[str]] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic data using multiple augmentation techniques.
    
    Args:
        features: Original feature array (n_samples, window_size, n_features)
        labels: Original labels (n_samples,)
        target_size: Target number of total samples (original + synthetic)
        methods: List of augmentation methods to use
                 Options: ['noise', 'time_warp', 'window_slice', 'magnitude_scale']
    
    Returns:
        Combined original and synthetic features and labels
    """
    if methods is None:
        methods = ['noise', 'time_warp', 'window_slice', 'magnitude_scale']
    
    n_original = len(features)
    n_synthetic_needed = max(0, target_size - n_original)
    
    if n_synthetic_needed == 0:
        print(f"Already have {n_original} samples, no synthetic data needed")
        return features, labels
    
    print(f"Generating {n_synthetic_needed} synthetic samples using {len(methods)} methods...")
    
    # Distribute synthetic samples across methods
    n_per_method = n_synthetic_needed // len(methods)
    
    synthetic_features_list = [features]
    synthetic_labels_list = [labels]
    
    for method in methods:
        if method == 'noise':
            aug_feat, aug_lab = add_noise_augmentation(
                features, labels, n_augmented=n_per_method
            )
            print(f"  ✓ Generated {len(aug_feat)} samples using noise augmentation")
        elif method == 'time_warp':
            aug_feat, aug_lab = time_warp_augmentation(
                features, labels, n_augmented=n_per_method
            )
            print(f"  ✓ Generated {len(aug_feat)} samples using time warp")
        elif method == 'window_slice':
            aug_feat, aug_lab = window_slicing_augmentation(
                features, labels, n_augmented=n_per_method
            )
            print(f"  ✓ Generated {len(aug_feat)} samples using window slicing")
        elif method == 'magnitude_scale':
            aug_feat, aug_lab = magnitude_scaling_augmentation(
                features, labels, n_augmented=n_per_method
            )
            print(f"  ✓ Generated {len(aug_feat)} samples using magnitude scaling")
        else:
            continue
        
        synthetic_features_list.append(aug_feat)
        synthetic_labels_list.append(aug_lab)
    
    # Combine all data
    combined_features = np.concatenate(synthetic_features_list, axis=0)
    combined_labels = np.concatenate(synthetic_labels_list, axis=0)
    
    # Shuffle
    indices = np.random.permutation(len(combined_features))
    combined_features = combined_features[indices]
    combined_labels = combined_labels[indices]
    
    print(f"✓ Total samples: {len(combined_features)} (original: {n_original}, synthetic: {len(combined_features) - n_original})")
    
    return combined_features, combined_labels
