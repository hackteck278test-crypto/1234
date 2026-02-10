"import httpx
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)


class GitLabService:
    def __init__(self):
        self.base_url = \"https://gitlab.com/api/v4\"
    
    def _parse_mr_url(self, mr_url: str) -> Optional[Dict[str, Any]]:
        \"\"\"Parse GitLab MR URL to extract project and MR IID\"\"\"
        try:
            # Example URL: https://gitlab.com/owner/project/-/merge_requests/123
            parsed = urlparse(mr_url)
            path_parts = parsed.path.split('/')
            
            # Find the merge_requests part
            if 'merge_requests' in path_parts:
                mr_index = path_parts.index('merge_requests')
                mr_iid = int(path_parts[mr_index + 1])
                
                # Get project path (everything before /-/)
                dash_index = path_parts.index('-')
                project_path = '/'.join(path_parts[1:dash_index])
                
                return {
                    \"project_path\": project_path,
                    \"mr_iid\": mr_iid
                }
            
            return None
        except Exception as e:
            logger.error(f\"Failed to parse MR URL: {str(e)}\")
            return None
    
    async def approve_merge_request(self, mr_url: str, gitlab_token: str) -> Dict[str, Any]:
        \"\"\"Approve a GitLab merge request\"\"\"
        try:
            mr_info = self._parse_mr_url(mr_url)
            if not mr_info:
                return {\"success\": False, \"error\": \"Invalid GitLab MR URL\"}
            
            project_path = quote(mr_info[\"project_path\"], safe='')
            mr_iid = mr_info[\"mr_iid\"]
            
            url = f\"{self.base_url}/projects/{project_path}/merge_requests/{mr_iid}/approve\"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={\"PRIVATE-TOKEN\": gitlab_token},
                    timeout=30.0
                )
                
                if response.status_code == 201 or response.status_code == 200:
                    logger.info(f\"Successfully approved MR {mr_url}\")
                    return {\"success\": True, \"data\": response.json()}
                else:
                    error_msg = f\"Failed to approve MR: {response.status_code} - {response.text}\"
                    logger.error(error_msg)
                    return {\"success\": False, \"error\": error_msg}
                    
        except Exception as e:
            error_msg = f\"Exception approving MR: {str(e)}\"
            logger.error(error_msg)
            return {\"success\": False, \"error\": error_msg}
    
    async def merge_merge_request(self, mr_url: str, gitlab_token: str) -> Dict[str, Any]:
        \"\"\"Merge a GitLab merge request\"\"\"
        try:
            mr_info = self._parse_mr_url(mr_url)
            if not mr_info:
                return {\"success\": False, \"error\": \"Invalid GitLab MR URL\"}
            
            project_path = quote(mr_info[\"project_path\"], safe='')
            mr_iid = mr_info[\"mr_iid\"]
            
            url = f\"{self.base_url}/projects/{project_path}/merge_requests/{mr_iid}/merge\"
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url,
                    headers={\"PRIVATE-TOKEN\": gitlab_token},
                    json={\"merge_when_pipeline_succeeds\": False},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f\"Successfully merged MR {mr_url}\")
                    return {\"success\": True, \"data\": response.json()}
                else:
                    error_msg = f\"Failed to merge MR: {response.status_code} - {response.text}\"
                    logger.error(error_msg)
                    return {\"success\": False, \"error\": error_msg}
                    
        except Exception as e:
            error_msg = f\"Exception merging MR: {str(e)}\"
            logger.error(error_msg)
            return {\"success\": False, \"error\": error_msg}
    
    async def decline_merge_request(self, mr_url: str, gitlab_token: str) -> Dict[str, Any]:
        \"\"\"Close/decline a GitLab merge request\"\"\"
        try:
            mr_info = self._parse_mr_url(mr_url)
            if not mr_info:
                return {\"success\": False, \"error\": \"Invalid GitLab MR URL\"}
            
            project_path = quote(mr_info[\"project_path\"], safe='')
            mr_iid = mr_info[\"mr_iid\"]
            
            url = f\"{self.base_url}/projects/{project_path}/merge_requests/{mr_iid}\"
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url,
                    headers={\"PRIVATE-TOKEN\": gitlab_token},
                    json={\"state_event\": \"close\"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f\"Successfully closed MR {mr_url}\")
                    return {\"success\": True, \"data\": response.json()}
                else:
                    error_msg = f\"Failed to close MR: {response.status_code} - {response.text}\"
                    logger.error(error_msg)
                    return {\"success\": False, \"error\": error_msg}
                    
        except Exception as e:
            error_msg = f\"Exception closing MR: {str(e)}\"
            logger.error(error_msg)
            return {\"success\": False, \"error\": error_msg}


# Singleton instance
_gitlab_service = None


def get_gitlab_service() -> GitLabService:
    global _gitlab_service
    if _gitlab_service is None:
        _gitlab_service = GitLabService()
    return _gitlab_service
"
