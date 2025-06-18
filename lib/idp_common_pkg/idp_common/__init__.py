# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Use true lazy loading for all submodules
__version__ = "0.1.0"

# Cache for lazy-loaded submodules
_submodules = {}


def __getattr__(name):
    """Lazy load submodules only when accessed"""
    if name in [
        "bedrock",
        "s3",
        "metrics",
        "image",
        "utils",
        "config",
        "ocr",
        "classification",
        "extraction",
        "evaluation",
        "assessment",
        "models",
        "reporting",
    ]:
        if name not in _submodules:
            _submodules[name] = __import__(f"idp_common.{name}", fromlist=[name])
        return _submodules[name]

    # Handle specific imports from models
    if name in ["get_config", "Document", "Page", "Section", "Status"]:
        if "models" not in _submodules:
            _submodules["models"] = __import__("idp_common.models", fromlist=["models"])
        return getattr(_submodules["models"], name)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Define what should be available when using "from idp_common import *"
__all__ = [
    "bedrock",
    "s3",
    "metrics",
    "image",
    "utils",
    "config",
    "ocr",
    "classification",
    "extraction",
    "evaluation",
    "assessment",
    "models",
    "reporting",
    "get_config",
    "Document",
    "Page",
    "Section",
    "Status",
]
