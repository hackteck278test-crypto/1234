"from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class ReviewIssue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file: str
    line: int
    severity: str  # \"error\", \"warning\", \"info\"
    message: str
    rule: str
    suggestion: Optional[str] = None


class ReviewData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mr_url: str
    mr_title: str
    author: str
    files_changed: int
    lines_added: int
    lines_removed: int
    review_time: str
    status: str  # \"passed\", \"warnings\", \"failed\"
    issues: List[ReviewIssue]
    summary: str
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)
    gitlab_token: Optional[str] = None
    project_id: Optional[str] = None
    merge_request_iid: Optional[int] = None


class SaveReviewRequest(BaseModel):
    review_data: ReviewData


class TelegramActionRequest(BaseModel):
    action: str  # \"approve\" or \"decline\"
    mr_url: str
    gitlab_token: str
    callback_query_id: str
    chat_id: str
    message_id: int


class GitLabActionRequest(BaseModel):
    mr_url: str
    gitlab_token: str
    action: str  # \"approve\" or \"merge\"


class UserSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    github_token: Optional[str] = None
    gitlab_token: Optional[str] = None
    telegram_enabled: bool = True
    email_enabled: bool = True
    auto_review_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SaveSettingsRequest(BaseModel):
    settings: UserSettings


class TelegramAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    review_id: str
    mr_url: str
    action: str  # \"approve\" or \"decline\"
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str  # \"pending\", \"success\", \"failed\"
    error_message: Optional[str] = None
"
