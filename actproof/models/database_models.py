"""
Database models for ActProof.ai using SQLAlchemy and Supabase.

This module defines the database schema for:
- Users (with subscription plans and limits)
- Scans (repository scans with results)
- Scan Components (AI models, datasets, dependencies)
- Notifications (real-time user notifications)
- API Keys (programmatic access)
- Audit Logs (compliance and debugging)
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Numeric,
    ForeignKey, CheckConstraint, Index, DECIMAL, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from pydantic import BaseModel, Field, validator

Base = declarative_base()


# ============================================================================
# Enums
# ============================================================================

class SubscriptionPlan(str, Enum):
    """Subscription plan types"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class ScanStatus(str, Enum):
    """Scan execution states"""
    PENDING = "pending"
    CLONING = "cloning"
    SCANNING = "scanning"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ComponentType(str, Enum):
    """AI component types"""
    MODEL = "model"
    DATASET = "dataset"
    DEPENDENCY = "dependency"


class RiskLevel(str, Enum):
    """Risk assessment levels (EU AI Act)"""
    MINIMAL = "MINIMAL"
    LIMITED = "LIMITED"
    HIGH = "HIGH"
    UNACCEPTABLE = "UNACCEPTABLE"


class NotificationType(str, Enum):
    """Notification types"""
    SCAN_COMPLETED = "scan_completed"
    SCAN_FAILED = "scan_failed"
    LIMIT_REACHED = "limit_reached"
    PLAN_UPGRADED = "plan_upgraded"
    SYSTEM_ALERT = "system_alert"


class Priority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ============================================================================
# SQLAlchemy Models
# ============================================================================

class User(Base):
    """User model with subscription and limits"""
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    company_name = Column(String(255))

    # Subscription
    subscription_plan = Column(
        String(50),
        default=SubscriptionPlan.FREE.value,
        nullable=False
    )

    # Limits
    scans_limit = Column(Integer, default=10, nullable=False)
    scans_used = Column(Integer, default=0, nullable=False)
    storage_limit_gb = Column(DECIMAL(10, 2), default=5.0, nullable=False)
    storage_used_gb = Column(DECIMAL(10, 2), default=0.0, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)

    # Preferences
    preferences = Column(JSONB, default={})

    # Relationships
    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('storage_used_gb <= storage_limit_gb', name='valid_storage'),
        CheckConstraint('scans_used <= scans_limit', name='valid_scans'),
        Index('idx_users_subscription', 'subscription_plan'),
    )

    def __repr__(self):
        return f"<User(email='{self.email}', plan='{self.subscription_plan}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'email': self.email,
            'full_name': self.full_name,
            'company_name': self.company_name,
            'subscription_plan': self.subscription_plan,
            'scans_limit': self.scans_limit,
            'scans_used': self.scans_used,
            'storage_limit_gb': float(self.storage_limit_gb),
            'storage_used_gb': float(self.storage_used_gb),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Scan(Base):
    """Repository scan model with AI-BOM and compliance results"""
    __tablename__ = 'scans'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User association (NULL for public scans)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))

    # Repository info
    repo_url = Column(String(500), nullable=False)
    repo_name = Column(String(255))
    repo_owner = Column(String(255))
    branch = Column(String(255), default='main')
    commit_sha = Column(String(40))

    # Status
    status = Column(String(50), default=ScanStatus.PENDING.value, nullable=False)

    # Execution metadata
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)

    # Results (JSONB)
    ai_bom = Column(JSONB)
    compliance_result = Column(JSONB)
    scan_summary = Column(JSONB, default={})

    # Statistics
    stats = Column(JSONB, default={})

    # Storage
    storage_path = Column(String(500))
    storage_size_mb = Column(DECIMAL(10, 2))

    # Error handling
    error_message = Column(Text)
    error_details = Column(JSONB)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Public/private
    is_public = Column(Boolean, default=False, nullable=False)

    # Additional metadata
    metadata = Column(JSONB, default={})

    # Relationships
    user = relationship("User", back_populates="scans")
    components = relationship("ScanComponent", back_populates="scan", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_scans_user_id', 'user_id'),
        Index('idx_scans_status', 'status'),
        Index('idx_scans_created_at', 'created_at'),
        Index('idx_scans_is_public', 'is_public'),
        Index('idx_scans_user_status', 'user_id', 'status'),
        # GIN indexes for JSONB (PostgreSQL specific)
        Index('idx_scans_ai_bom', 'ai_bom', postgresql_using='gin'),
        Index('idx_scans_compliance', 'compliance_result', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<Scan(id='{self.id}', repo='{self.repo_name}', status='{self.status}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'repo_url': self.repo_url,
            'repo_name': self.repo_name,
            'repo_owner': self.repo_owner,
            'branch': self.branch,
            'commit_sha': self.commit_sha,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'ai_bom': self.ai_bom,
            'compliance_result': self.compliance_result,
            'scan_summary': self.scan_summary,
            'stats': self.stats,
            'storage_path': self.storage_path,
            'storage_size_mb': float(self.storage_size_mb) if self.storage_size_mb else None,
            'error_message': self.error_message,
            'is_public': self.is_public,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ScanComponent(Base):
    """AI components detected in scans (denormalized for fast queries)"""
    __tablename__ = 'scan_components'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey('scans.id', ondelete='CASCADE'), nullable=False)

    # Component type
    component_type = Column(String(50), nullable=False)

    # Component info
    name = Column(String(255), nullable=False)
    provider = Column(String(100))
    component_version = Column(String(100))
    license = Column(String(100))

    # Details (JSONB)
    details = Column(JSONB, default={})

    # Risk assessment
    risk_level = Column(String(50))

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    scan = relationship("Scan", back_populates="components")

    __table_args__ = (
        Index('idx_scan_components_scan_id', 'scan_id'),
        Index('idx_scan_components_type', 'component_type'),
        Index('idx_scan_components_provider', 'provider'),
    )

    def __repr__(self):
        return f"<ScanComponent(name='{self.name}', type='{self.component_type}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'scan_id': str(self.scan_id),
            'component_type': self.component_type,
            'name': self.name,
            'provider': self.provider,
            'component_version': self.component_version,
            'license': self.license,
            'details': self.details,
            'risk_level': self.risk_level,
        }


class Notification(Base):
    """User notifications for real-time updates"""
    __tablename__ = 'notifications'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Type
    type = Column(String(50), nullable=False)

    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text)

    # Metadata
    data = Column(JSONB, default={})

    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True))

    # Priority
    priority = Column(String(20), default=Priority.NORMAL.value, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index('idx_notifications_user_id', 'user_id'),
        Index('idx_notifications_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<Notification(type='{self.type}', title='{self.title}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = 'api_keys'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # API Key
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(10), nullable=False)

    # Metadata
    name = Column(String(255))
    description = Column(Text)

    # Permissions
    scopes = Column(JSONB, default=["read", "scan"])

    # Limits
    rate_limit = Column(Integer, default=60)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index('idx_api_keys_user_id', 'user_id'),
        Index('idx_api_keys_key_hash', 'key_hash'),
    )

    def __repr__(self):
        return f"<APIKey(name='{self.name}', prefix='{self.key_prefix}')>"


class AuditLog(Base):
    """Audit logs for compliance and debugging"""
    __tablename__ = 'audit_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Actor
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    api_key_id = Column(UUID(as_uuid=True), ForeignKey('api_keys.id', ondelete='SET NULL'))

    # Action
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))

    # Details
    details = Column(JSONB, default={})

    # Context
    ip_address = Column(INET)
    user_agent = Column(Text)

    # Timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_created_at', 'created_at'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
    )

    def __repr__(self):
        return f"<AuditLog(action='{self.action}', resource='{self.resource_type}')>"


# ============================================================================
# Pydantic Models for API Validation
# ============================================================================

class UserCreate(BaseModel):
    """Schema for creating a new user"""
    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    subscription_plan: SubscriptionPlan = SubscriptionPlan.FREE

    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    subscription_plan: str
    scans_limit: int
    scans_used: int
    storage_limit_gb: float
    storage_used_gb: float
    is_active: bool
    created_at: str

    class Config:
        orm_mode = True


class ScanCreate(BaseModel):
    """Schema for creating a new scan"""
    repo_url: str
    branch: Optional[str] = "main"
    is_public: bool = False
    metadata: Optional[Dict[str, Any]] = {}

    @validator('repo_url')
    def repo_url_must_be_valid(cls, v):
        if not v.startswith(('https://github.com/', 'https://gitlab.com/')):
            raise ValueError('Only GitHub and GitLab URLs are supported')
        return v


class ScanUpdate(BaseModel):
    """Schema for updating scan status"""
    status: Optional[ScanStatus] = None
    ai_bom: Optional[Dict[str, Any]] = None
    compliance_result: Optional[Dict[str, Any]] = None
    scan_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class ScanResponse(BaseModel):
    """Schema for scan response"""
    id: str
    user_id: Optional[str]
    repo_url: str
    repo_name: Optional[str]
    status: str
    started_at: str
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    scan_summary: Optional[Dict[str, Any]]
    is_public: bool
    created_at: str

    class Config:
        orm_mode = True


class NotificationCreate(BaseModel):
    """Schema for creating notification"""
    user_id: str
    type: NotificationType
    title: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = {}
    priority: Priority = Priority.NORMAL


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: str
    type: str
    title: str
    message: Optional[str]
    data: Optional[Dict[str, Any]]
    is_read: bool
    priority: str
    created_at: str

    class Config:
        orm_mode = True


# ============================================================================
# Database Helper Functions
# ============================================================================

def init_database(engine):
    """Initialize database with all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_database(engine):
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("❌ Database tables dropped")
