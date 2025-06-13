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
__version__ = "0.4.2"

from .client import Client, AutoShardedClient
from .models import Message, User, Reaction, AuditLogEntry
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
from .enums import GatewayIntent, GatewayOpcode
from .error_handler import setup_global_error_handler
from .hybrid_context import HybridContext
from .ext import tasks
from .logging_config import setup_logging

import logging


__all__ = [
    "Client",
    "AutoShardedClient",
    "Message",
    "User",
    "Reaction",
    "AuditLogEntry",
    "VoiceClient",
    "AudioSource",
    "FFmpegAudioSource",
    "Typing",
    "DisagreementException",
    "HTTPException",
    "GatewayException",
    "AuthenticationError",
    "Forbidden",
    "NotFound",
    "Color",
    "utcnow",
    "message_pager",
    "GatewayIntent",
    "GatewayOpcode",
    "setup_global_error_handler",
    "HybridContext",
    "tasks",
    "setup_logging",
]


# Configure a default logger if none has been configured yet
if not logging.getLogger().hasHandlers():
    setup_logging(logging.INFO)
