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
    ],
    "get_config",
    "Document",
    "Page",
    "Section",
    "Status",
]
