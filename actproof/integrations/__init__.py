"""
Integrazioni Fase 4: AWS Marketplace, GitHub Actions, Middleware
"""

from actproof.integrations.aws_marketplace import AWSMarketplaceClient, MeteringRecord
from actproof.integrations.github_action import GitHubActionHandler
from actproof.integrations.audit_middleware import AuditMiddleware, AuditLog, AuditEventType

__all__ = [
    "AWSMarketplaceClient",
    "MeteringRecord",
    "GitHubActionHandler",
    "AuditMiddleware",
    "AuditLog",
    "AuditEventType",
]
