"""User context processor."""

import logging
import hashlib
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class UserContextProcessor:
    """Process and enrich user context."""

    def __init__(self, hash_sensitive: bool = True):
        self.hash_sensitive = hash_sensitive

    def process_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user data.
        
        Args:
            user_data: Raw user data
            
        Returns:
            Enriched user context
        """
        context = {}

        # Process user ID
        if "id" in user_data:
            context["id"] = str(user_data["id"])

        # Process email
        if "email" in user_data:
            email = user_data["email"]
            if self.hash_sensitive:
                context["email_hash"] = self._hash_value(email)
                context["email_domain"] = self._extract_email_domain(email)
            else:
                context["email"] = email

        # Process username
        if "username" in user_data:
            context["username"] = user_data["username"]

        # Process name
        if "name" in user_data:
            context["name"] = user_data["name"]
        elif "first_name" in user_data or "last_name" in user_data:
            name_parts = []
            if "first_name" in user_data:
                name_parts.append(user_data["first_name"])
            if "last_name" in user_data:
                name_parts.append(user_data["last_name"])
            context["name"] = " ".join(name_parts)

        # Process phone
        if "phone" in user_data:
            phone = user_data["phone"]
            if self.hash_sensitive:
                context["phone_hash"] = self._hash_value(phone)
            else:
                context["phone"] = phone

        # Add user metadata
        context["metadata"] = self._extract_metadata(user_data)

        return context

    def _hash_value(self, value: str) -> str:
        """Hash a sensitive value.
        
        Args:
            value: Value to hash
            
        Returns:
            SHA256 hash
        """
        return hashlib.sha256(value.encode()).hexdigest()

    def _extract_email_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address.
        
        Args:
            email: Email address
            
        Returns:
            Email domain or None
        """
        if "@" in email:
            return email.split("@")[1]
        return None

    def _extract_metadata(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user metadata.
        
        Args:
            user_data: User data
            
        Returns:
            User metadata
        """
        metadata = {}

        # Common metadata fields
        metadata_fields = [
            "role",
            "account_type",
            "subscription_tier",
            "created_at",
            "last_login",
            "is_active",
            "is_verified",
            "locale",
            "timezone",
        ]

        for field in metadata_fields:
            if field in user_data:
                metadata[field] = user_data[field]

        return metadata

    def enrich_with_session(self, user_context: Dict[str, Any], session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich user context with session information.
        
        Args:
            user_context: User context
            session_data: Session data
            
        Returns:
            Enriched user context
        """
        if "session" not in user_context:
            user_context["session"] = {}

        # Add session ID
        if "id" in session_data:
            if self.hash_sensitive:
                user_context["session"]["id_hash"] = self._hash_value(str(session_data["id"]))
            else:
                user_context["session"]["id"] = str(session_data["id"])

        # Add session metadata
        session_fields = [
            "created_at",
            "last_activity",
            "ip_address",
            "user_agent",
        ]

        for field in session_fields:
            if field in session_data:
                user_context["session"][field] = session_data[field]

        return user_context
