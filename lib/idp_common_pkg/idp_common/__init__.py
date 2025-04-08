# Import submodules for easier access
from idp_common import bedrock
from idp_common import s3
from idp_common import metrics
from idp_common import image
from idp_common import utils
from idp_common import config
from idp_common import ocr
from idp_common import classification

# Expose key functions at the package level for backward compatibility
from idp_common.config import get_config

__version__ = "0.1.0"