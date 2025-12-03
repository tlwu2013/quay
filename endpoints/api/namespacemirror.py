import logging
from flask import request
from app import app
from endpoints.api import (
    ApiResource,
    path_param,
    resource,
    validate_json_request,
    require_scope,
)
from endpoints.exception import NotFound, Unauthorized
from data.model import organization as organization_model, InvalidRobotException
from auth.auth_context import get_authenticated_user
from auth.permissions import AdministerOrganizationPermission
from auth import scopes

logger = logging.getLogger(__name__)

create_mirror_schema = {
    "type": "object",
    "description": "Configuration for organization mirroring",
    "required": ["external_registry", "external_namespace"],
    "properties": {
        "external_registry": {
            "type": "string",
            "description": "URL of the external registry (e.g., https://harbor.example.com)"
        },
        "external_namespace": {
            "type": "string",
            "description": "Namespace/Project in the external registry"
        },
        "external_registry_username": {
            "type": ["string", "null"],
            "description": "Username for external registry authentication"
        },
        "external_registry_password": {
            "type": ["string", "null"],
            "description": "Password for external registry authentication"
        },
        "sync_interval": {
            "type": "integer",
            "description": "Sync interval in seconds",
            "default": 86400
        },
        "repo_filter_type": {
            "type": "string",
            "enum": ["regex", "list"],
            "default": "regex"
        },
        "repo_filter_value": {
            "type": ["string", "null"],
            "description": "Filter value (regex string or comma-separated list)"
        },
        "internal_robot": {
            "type": ["string", "null"],
            "description": "Robot account name to use for mirroring operations"
        },
        "is_enabled": {
            "type": "boolean",
            "default": True
        }
    }
}

@resource("/v1/organization/<orgname>/mirror")
@path_param("orgname", "The name of the organization")
class OrganizationMirrorResource(ApiResource):
    schemas = {
        "CreateOrganizationMirror": create_mirror_schema
    }
    @require_scope(scopes.ORG_ADMIN)
    def get(self, orgname):
        """
        Get the organization mirroring configuration.
        """
        from data.model import namespace_mirror
        from data.model import organization as organization_model

        if not app.config.get("FEATURE_NAMESPACE_MIRROR", True):
            raise NotFound()

        if not AdministerOrganizationPermission(orgname).can():
            raise Unauthorized()

        org = organization_model.get_organization(orgname)
        if not org:
            raise NotFound()
        
        config = namespace_mirror.get_namespace_mirror_config(org)
        if not config:
            return {}, 200

        return {
            "external_registry": config.external_registry,
            "external_namespace": config.external_namespace,
            "external_registry_username": config.external_registry_username.decrypt() if config.external_registry_username else None,
            "sync_interval": config.sync_interval,
            "repo_filter_type": config.repo_filter_type,
            "repo_filter_value": config.repo_filter_value,
            "internal_robot": config.internal_robot.username if config.internal_robot else None,
            "is_enabled": config.is_enabled,
            "sync_status": config.sync_status,
            "sync_message": config.sync_message,
            "last_sync_start": config.last_sync_start.isoformat() if config.last_sync_start else None
        }

    @require_scope(scopes.ORG_ADMIN)
    @validate_json_request("CreateOrganizationMirror")
    def post(self, orgname):
        """
        Create or update the organization mirroring configuration.
        """
        from data.model import namespace_mirror
        from data.model import user as user_model

        if not app.config.get("FEATURE_NAMESPACE_MIRROR", True):
            raise NotFound()

        if not AdministerOrganizationPermission(orgname).can():
            raise Unauthorized()

        org = organization_model.get_organization(orgname)
        if not org:
            raise NotFound()

        data = request.get_json()
        
        internal_robot = None
        if data.get("internal_robot"):
            try:
                internal_robot = user_model.lookup_robot(data["internal_robot"])
            except InvalidRobotException:
                raise NotFound("Robot account not found")

        config = namespace_mirror.create_or_update_namespace_mirror_config(
            organization=org,
            external_registry=data["external_registry"],
            external_namespace=data["external_namespace"],
            external_registry_username=data.get("external_registry_username"),
            external_registry_password=data.get("external_registry_password"),
            sync_interval=data.get("sync_interval", 86400),
            repo_filter_type=data.get("repo_filter_type", "regex"),
            repo_filter_value=data.get("repo_filter_value"),
            is_enabled=data.get("is_enabled", True),
            internal_robot=internal_robot
        )

        return {
            "message": "Configuration updated"
        }, 201


@resource("/v1/organization/<orgname>/mirror/sync-now")
@path_param("orgname", "The name of the organization")
class OrganizationMirrorSyncNowResource(ApiResource):
    @require_scope(scopes.ORG_ADMIN)
    def post(self, orgname):
        """
        Trigger immediate synchronization for the organization mirroring configuration.
        """
        from data.model import namespace_mirror

        if not app.config.get("FEATURE_NAMESPACE_MIRROR", True):
            raise NotFound()

        if not AdministerOrganizationPermission(orgname).can():
            raise Unauthorized()

        org = organization_model.get_organization(orgname)
        if not org:
            raise NotFound()

        config = namespace_mirror.get_namespace_mirror_config(org)
        if not config:
            raise NotFound()

        if namespace_mirror.update_namespace_mirror_sync_status_to_sync_now(config):
            return {"message": "Sync triggered successfully"}, 200
        else:
            return {"error": "Sync is already in progress"}, 409
