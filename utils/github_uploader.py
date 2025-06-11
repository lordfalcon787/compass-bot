import aiohttp
import base64
import os
import json
from typing import Optional
from datetime import datetime

class GitHubUploader:
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
        
    async def upload_file(self, file_content: bytes, file_path: str, commit_message: Optional[str] = None) -> str:
        if not commit_message:
            commit_message = f"Upload {file_path}"
            
        encoded_content = base64.b64encode(file_content).decode('utf-8')
        
        url = f"{self.api_url}/{file_path}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        sha = None
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    existing_file = await response.json()
                    sha = existing_file["sha"]
        
        data = {
            "message": commit_message,
            "content": encoded_content
        }
        
        if sha:
            data["sha"] = sha
            
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    return result["content"]["download_url"]
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to upload file: {response.status} - {error_text}")
    
    async def upload_transcript(self, transcript_content: bytes, channel_name: str, timestamp: datetime) -> str:
        filename = f"{channel_name}.html"
        file_path = f"transcripts/{filename}"
        commit_message = f"Add transcript for #{channel_name}"
        
        return await self.upload_file(transcript_content, file_path, commit_message)

def get_github_uploader() -> Optional[GitHubUploader]:
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        github_config = config.get('github', {})
        token = github_config.get('token')
        owner = github_config.get('owner')
        repo = github_config.get('repo')
        
        if not all([token, owner, repo]):
            print("Warning: GitHub configuration incomplete in config.json. Need 'github.token', 'github.owner', and 'github.repo'.")
            return None
            
        return GitHubUploader(token, owner, repo)
        
    except FileNotFoundError:
        print("Warning: config.json file not found.")
        return None
    except json.JSONDecodeError:
        print("Warning: Invalid JSON in config.json file.")
        return None
    except Exception as e:
        print(f"Warning: Error loading GitHub config: {e}")
        return None