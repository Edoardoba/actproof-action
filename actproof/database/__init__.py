"""
Database module for ActProof.ai

This module provides database access and management functionality.
"""

from .supabase_manager import SupabaseManager, get_db_manager

__all__ = ['SupabaseManager', 'get_db_manager']
