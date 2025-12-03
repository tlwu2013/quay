import logging
import os
import time
import re
import datetime

from app import app
from workers.worker import Worker
from workers.gunicorn_worker import GunicornWorker
from data.database import NamespaceMirrorConfig, RepoMirrorConfig as DBRepoMirrorConfig
from util.namespacemirror.client import get_client
from data.model import repository, repo_mirror
from util.log import logfile_path

logger = logging.getLogger(__name__)

class NamespaceMirrorWorker(Worker):
    def __init__(self):
        super(NamespaceMirrorWorker, self).__init__()
        self.add_operation(self.sync_namespaces, 60)

    def sync_namespaces(self):
        try:
            configs = NamespaceMirrorConfig.select().where(
                NamespaceMirrorConfig.is_enabled == True
            )
            
            now = datetime.datetime.utcnow()
            
            for config in configs:
                should_run = False
                if config.sync_status == 'sync_now':
                    should_run = True
                elif not config.last_sync_start:
                    should_run = True
                else:
                    next_run = config.last_sync_start + datetime.timedelta(seconds=config.sync_interval)
                    if now >= next_run:
                        should_run = True

                if should_run:
                    self.perform_sync(config)
                    
        except Exception as e:
            logger.exception("Error in NamespaceMirrorWorker loop")

    def perform_sync(self, config):
        logger.info(f"Starting namespace sync for {config.organization.username}")
        config.sync_status = 'syncing'
        config.last_sync_start = datetime.datetime.utcnow()
        config.save()
        
        try:
            username = config.external_registry_username.decrypt() if config.external_registry_username else None
            password = config.external_registry_password.decrypt() if config.external_registry_password else None
            
            client = get_client(
                config.external_registry, 
                username,
                password,
                verify_tls=True
            )
            
            repos = client.list_repositories(config.external_namespace)
            logger.info(f"Found {len(repos)} repositories in external namespace {config.external_namespace}")
            
            # Filter
            if config.repo_filter_value:
                if config.repo_filter_type == 'regex':
                    try:
                        pattern = re.compile(config.repo_filter_value)
                        repos = [r for r in repos if pattern.match(r)]
                    except Exception as ex:
                         logger.error(f"Invalid regex for namespace mirror {config.id}: {ex}")
                elif config.repo_filter_type == 'list':
                    allowed = set(r.strip() for r in config.repo_filter_value.split(','))
                    repos = [r for r in repos if r in allowed]
            
            logger.info(f"Syncing {len(repos)} repositories after filter")
            
            for repo_name in repos:
                # Ensure repo exists in local org
                local_repo = repository.get_repository(config.organization.username, repo_name)
                if not local_repo:
                    if not config.internal_robot:
                        logger.error(f"No internal robot configured for namespace mirror {config.id}. Cannot create repo {repo_name}.")
                        continue
                        
                    local_repo = repository.create_repository(
                        config.organization.username, 
                        repo_name, 
                        config.internal_robot,
                        description=f"Mirrored from {config.external_registry}/{config.external_namespace}/{repo_name}"
                    )
                    if not local_repo:
                        logger.error(f"Failed to create local repository {repo_name}")
                        continue
                
                # Check if mirror config exists
                try:
                    current_mirror = DBRepoMirrorConfig.get(repository=local_repo)
                except DBRepoMirrorConfig.DoesNotExist:
                    current_mirror = None
                
                if not current_mirror:
                    # Create external reference in Docker registry format (without https://)
                    registry_base = config.external_registry.replace('https://', '').replace('http://', '').rstrip('/')
                    external_ref = f"{registry_base}/{config.external_namespace}/{repo_name}"
                    rule = repo_mirror.create_mirroring_rule(local_repo, ["**"])
                    
                    repo_mirror.enable_mirroring_for_repository(
                        local_repo,
                        root_rule=rule,
                        internal_robot=config.internal_robot,
                        external_reference=external_ref,
                        sync_interval=config.sync_interval,
                        skopeo_timeout_interval=600,
                        external_registry_username=config.external_registry_username,
                        external_registry_password=config.external_registry_password,
                        is_enabled=True
                    )

                    # Trigger immediate sync for the newly created mirror
                    mirror_config = repo_mirror.get_mirror(local_repo)
                    if mirror_config and repo_mirror.update_sync_status_to_sync_now(mirror_config):
                        logger.info(f"Triggered immediate sync for {local_repo.name}")

                    logger.info(f"Created mirror config for {local_repo.name}")

            config.sync_status = 'success'
            config.sync_message = f"Successfully synced {len(repos)} repositories"
            config.save()
            
        except Exception as e:
            logger.exception(f"Namespace sync failed for {config.organization.username}")
            config.sync_status = 'failure'
            config.sync_message = str(e)
            config.save()


def create_gunicorn_worker():
    worker = GunicornWorker(__name__, app, NamespaceMirrorWorker(), True)
    return worker

if __name__ == "__main__":
    logging.config.fileConfig(logfile_path(debug=False), disable_existing_loggers=False)
    worker = NamespaceMirrorWorker()
    worker.start()

