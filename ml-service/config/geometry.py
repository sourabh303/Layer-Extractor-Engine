"""
Centralized configuration for Geometry Cleanup constants.
These parameters guarantee all generated pattern designs exclude fabric-related textures,
curves, or folds, resulting in strictly flat design outputs with hard-vertex linear polygons.
"""

# OpenCV K-Means configuration
# Max clusters reduces gradient variance, flattening the image into solid blocks
KMEANS_MAX_CLUSTERS = 12

# OpenCV approxPolyDP epsilon multiplier
# Multiplied by the arcLength of each contour to explicitly remove curves and wavy folds
APPROX_POLY_DP_EPSILON_MULTIPLIER = 0.02

# Enforces that NO Bezier curves are present in outputs
# (This constant is used as a flag throughout the pipeline vectorization step)
ALLOW_BEZIER_CURVES = False
