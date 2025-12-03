import requests
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class RegistryClient:
    def __init__(self, registry_url, username=None, password=None, verify_tls=True):
        self.registry_url = registry_url
        self.username = username
        self.password = password
        self.verify_tls = verify_tls
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
        self.session.verify = verify_tls

    def list_repositories(self, namespace):
        raise NotImplementedError

class HarborClient(RegistryClient):
    def list_repositories(self, namespace):
        # Harbor V2 API
        # GET /api/v2.0/projects/{project_name}/repositories
        base_url = self.registry_url.rstrip("/")
        
        # Handle cases where user provides full API url or just base domain
        if "/api/v2.0" in base_url:
             api_url = base_url
        else:
             api_url = f"{base_url}/api/v2.0"
        
        url = f"{api_url}/projects/{namespace}/repositories"
        repos = []
        page = 1
        page_size = 100
        
        while True:
            try:
                resp = self.session.get(url, params={"page": page, "page_size": page_size})
                resp.raise_for_status()
                data = resp.json()
                if not data:
                    break
                
                for repo in data:
                    # Harbor returns repo name like "project/repo".
                    repo_name = repo["name"]
                    # Strip project name if it's included
                    if repo_name.startswith(f"{namespace}/"):
                        repo_name = repo_name[len(namespace)+1:]
                    repos.append(repo_name)
                
                page += 1
            except Exception as e:
                logger.error(f"Failed to list repositories from Harbor: {e}")
                raise

        return repos

class QuayClient(RegistryClient):
    def list_repositories(self, namespace):
        # Quay API
        # GET /api/v1/repository?namespace={namespace}
        base_url = self.registry_url.rstrip("/")
        url = f"{base_url}/api/v1/repository"
        
        repos = []
        next_page = None
        
        while True:
            params = {"namespace": namespace, "public": "true"}
            if next_page:
                params["next_page"] = next_page

            try:
                resp = self.session.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                
                for repo in data.get("repositories", []):
                    repos.append(repo["name"])
                
                next_page = data.get("next_page")
                if not next_page:
                    break
            except Exception as e:
                logger.error(f"Failed to list repositories from Quay: {e}")
                raise
                
        return repos

def get_client(registry_url, username=None, password=None, verify_tls=True):
    session = requests.Session()
    session.verify = verify_tls
    if username and password:
        session.auth = (username, password)
        
    # Try to detect Harbor
    try:
        base = registry_url.rstrip('/')
        resp = session.get(f"{base}/api/v2.0/systeminfo", timeout=5)
        if resp.status_code == 200:
            return HarborClient(registry_url, username, password, verify_tls)
    except:
        pass
    
    # Default to Quay as it's the other likely option or fallback
    return QuayClient(registry_url, username, password, verify_tls)

