# disagreement/__init__.py

"""
Disagreement
~~~~~~~~~~~~

A Python library for interacting with the Discord API.

:copyright: (c) 2025 Slipstream
:license: BSD 3-Clause License, see LICENSE for more details.
"""

__title__ = "disagreement"
__author__ = "Slipstream"
__license__ = "BSD 3-Clause License"
__copyright__ = "Copyright 2025 Slipstream"
__version__ = "0.1.0rc3"

from .client import Client, AutoShardedClient
from .models import Message, User, Reaction
from .voice_client import VoiceClient
from .audio import AudioSource, FFmpegAudioSource
from .typing import Typing
from .errors import (
    DisagreementException,
    HTTPException,
    GatewayException,
    AuthenticationError,
    Forbidden,
    NotFound,
)
from .color import Color
from .utils import utcnow, message_pager
from .enums import GatewayIntent, GatewayOpcode  # Export enums
from .error_handler import setup_global_error_handler
from .hybrid_context import HybridContext
from .ext import tasks
from .logging_config import setup_logging

import logging


# Configure a default logger if none has been configured yet
if not logging.getLogger().hasHandlers():
    setup_logging(logging.INFO)
