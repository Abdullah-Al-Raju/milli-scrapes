"""
Milli-Scrapes Notification Subsystem.
Dispatches real-time email alerts with in-memory visual proof attachments.
"""

from .email import EmailNotifier

__all__ = ["EmailNotifier"]
