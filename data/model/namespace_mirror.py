from data.database import NamespaceMirrorConfig, User, db_transaction
from data.model import DataModelException
from data.fields import DecryptedValue


def get_namespace_mirror_config(organization):
    try:
        return NamespaceMirrorConfig.get(organization=organization)
    except NamespaceMirrorConfig.DoesNotExist:
        return None


def update_namespace_mirror_sync_status_to_sync_now(config):
    """
    Update the sync status to 'sync_now' to trigger immediate syncing.
    Returns True if successful, False if already syncing.
    """
    if config.sync_status == 'syncing':
        return False

    config.sync_status = 'sync_now'
    config.save()
    return True


def create_or_update_namespace_mirror_config(
    organization,
    external_registry,
    external_namespace,
    external_registry_username=None,
    external_registry_password=None,
    sync_interval=86400,
    repo_filter_type="regex",
    repo_filter_value=None,
    internal_robot=None,
    is_enabled=True,
):
    # Convert empty strings to None for encrypted fields
    if external_registry_username == "":
        external_registry_username = None
    if external_registry_password == "":
        external_registry_password = None
    if repo_filter_value == "":
        repo_filter_value = None
    with db_transaction():
        try:
            config = NamespaceMirrorConfig.get(organization=organization)
            config.external_registry = external_registry
            config.external_namespace = external_namespace
            if external_registry_username is not None:
                config.external_registry_username = DecryptedValue(external_registry_username)
            else:
                config.external_registry_username = None
            if external_registry_password is not None:
                config.external_registry_password = DecryptedValue(external_registry_password)
            else:
                config.external_registry_password = None
            config.sync_interval = sync_interval
            config.repo_filter_type = repo_filter_type
            config.repo_filter_value = repo_filter_value
            if internal_robot:
                config.internal_robot = internal_robot
            config.is_enabled = is_enabled
            config.save()
            return config
        except NamespaceMirrorConfig.DoesNotExist:
            username = DecryptedValue(external_registry_username) if external_registry_username is not None else None
            password = DecryptedValue(external_registry_password) if external_registry_password is not None else None
            
            return NamespaceMirrorConfig.create(
                organization=organization,
                external_registry=external_registry,
                external_namespace=external_namespace,
                external_registry_username=username,
                external_registry_password=password,
                sync_interval=sync_interval,
                repo_filter_type=repo_filter_type,
                repo_filter_value=repo_filter_value,
                internal_robot=internal_robot,
                is_enabled=is_enabled
            )

