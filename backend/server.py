from fastapi import FastAPI, APIRouter, HTTPException, Request

from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

import uuid
from datetime import datetime


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix=\"/api\")


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get(\"/\")
async def root():
    return {\"message\": \"GitLab MR Review API\"}

@api_router.post(\"/status\", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get(\"/status\", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event(\"shutdown\")
async def shutdown_db_client():
    client.close()" --new-str "from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import json

# Import our custom modules
from models import (
    ReviewData, SaveReviewRequest, TelegramActionRequest,
    GitLabActionRequest, UserSettings, SaveSettingsRequest, TelegramAction
)
from telegram_service import get_telegram_service
from gitlab_service import get_gitlab_service
from supabase_client import get_supabase


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix=\"/api\")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str


# ==================== EXISTING ROUTES ====================

@api_router.get(\"/\")
async def root():
    return {\"message\": \"GitLab MR Review API\"}

@api_router.post(\"/status\", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get(\"/status\", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


# ==================== REVIEW ROUTES ====================

@api_router.post(\"/reviews/save\")
async def save_review(request: SaveReviewRequest):
    \"\"\"Save review data to Supabase\"\"\"
    try:
        supabase = get_supabase()
        review_dict = request.review_data.dict()

        # Convert datetime objects to ISO strings
        if 'reviewed_at' in review_dict and isinstance(review_dict['reviewed_at'], datetime):
            review_dict['reviewed_at'] = review_dict['reviewed_at'].isoformat()
        
        # Convert issues to dict format
        review_dict['issues'] = [issue.dict() if hasattr(issue, 'dict') else issue 
                                  for issue in review_dict.get('issues', [])]
        
        # Save to Supabase
        result = supabase.table('reviews').insert(review_dict).execute()
        
        logger.info(f\"Saved review to Supabase: {request.review_data.id}\")
        return {\"success\": True, \"review_id\": request.review_data.id, \"data\": result.data}
    
    except Exception as e:
        logger.error(f\"Failed to save review to Supabase: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get(\"/reviews/history\")
async def get_review_history(limit: int = 50):
    \"\"\"Get review history from Supabase\"\"\"
    try:
        supabase = get_supabase()
        result = supabase.table('reviews').select('*').order('reviewed_at', desc=True).limit(limit).execute()
        
        return {\"success\": True, \"reviews\": result.data}
    
    except Exception as e:
        logger.error(f\"Failed to get review history: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get(\"/reviews/{review_id}\")
async def get_review(review_id: str):
    \"\"\"Get specific review from Supabase\"\"\"
    try:
        supabase = get_supabase()
        result = supabase.table('reviews').select('*').eq('id', review_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=\"Review not found\")
        
        return {\"success\": True, \"review\": result.data[0]}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f\"Failed to get review: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TELEGRAM ROUTES ====================

@api_router.post(\"/telegram/send-notification\")
async def send_telegram_notification(review: ReviewData):
    \"\"\"Send Telegram notification with review details and action buttons\"\"\"
    try:
        telegram_service = get_telegram_service()
        success = await telegram_service.send_review_notification(review)
        
        if success:
            return {\"success\": True, \"message\": \"Telegram notification sent\"}
        else:
            raise HTTPException(status_code=500, detail=\"Failed to send Telegram notification\")
    
    except Exception as e:
        logger.error(f\"Error in send_telegram_notification: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post(\"/telegram/webhook\")
async def telegram_webhook(request: Request):
    \"\"\"Handle Telegram webhook callbacks (button clicks)\"\"\"
    try:
        data = await request.json()
        logger.info(f\"Received Telegram webhook: {data}\")
        
        # Extract callback query
        callback_query = data.get('callback_query')
        if not callback_query:
            return {\"success\": True}
        
        callback_data = json.loads(callback_query['data'])
        action = callback_data.get('action')
        review_id = callback_data.get('review_id')
        mr_url = callback_data.get('mr_url')
        
        callback_query_id = callback_query['id']
        chat_id = str(callback_query['message']['chat']['id'])
        message_id = callback_query['message']['message_id']
        
        # Get review from Supabase to get GitLab token
        supabase = get_supabase()
        review_result = supabase.table('reviews').select('*').eq('id', review_id).execute()
        
        if not review_result.data:
            telegram_service = get_telegram_service()
            await telegram_service.answer_callback_query(
                callback_query_id, 
                \"❌ Review not found\"
            )
            return {\"success\": False, \"error\": \"Review not found\"}
        
        review = review_result.data[0]
        gitlab_token = review.get('gitlab_token')
        
        if not gitlab_token:
            telegram_service = get_telegram_service()
            await telegram_service.answer_callback_query(
                callback_query_id,
                \"❌ GitLab token not found. Please configure in settings.\"
            )
            return {\"success\": False, \"error\": \"GitLab token not configured\"}
        
        # Execute action
        gitlab_service = get_gitlab_service()
        telegram_service = get_telegram_service()
        
        if action == \"approve\":
            # Approve and merge
            approve_result = await gitlab_service.approve_merge_request(mr_url, gitlab_token)
            
            if approve_result['success']:
                merge_result = await gitlab_service.merge_merge_request(mr_url, gitlab_token)
                
                if merge_result['success']:
                    await telegram_service.answer_callback_query(
                        callback_query_id,
                        \"✅ Merge request approved and merged successfully!\"
                    )
                    
                    # Log action to Supabase
                    action_record = TelegramAction(
                        review_id=review_id,
                        mr_url=mr_url,
                        action=\"approve\",
                        status=\"success\"
                    )
                    supabase.table('telegram_actions').insert(action_record.dict()).execute()
                    
                    return {\"success\": True, \"action\": \"approved_and_merged\"}
                else:
                    await telegram_service.answer_callback_query(
                        callback_query_id,
                        f\"⚠️ Approved but merge failed: {merge_result.get('error', 'Unknown error')}\"
                    )
                    return {\"success\": False, \"error\": merge_result.get('error')}
            else:
                await telegram_service.answer_callback_query(
                    callback_query_id,
                    f\"❌ Failed to approve: {approve_result.get('error', 'Unknown error')}\"
                )
                return {\"success\": False, \"error\": approve_result.get('error')}
        
        elif action == \"decline\":
            # Close/decline MR
            decline_result = await gitlab_service.decline_merge_request(mr_url, gitlab_token)
            
            if decline_result['success']:
                await telegram_service.answer_callback_query(
                    callback_query_id,
                    \"❌ Merge request declined successfully!\"
                )
                
                # Log action to Supabase
                action_record = TelegramAction(
                    review_id=review_id,
                    mr_url=mr_url,
                    action=\"decline\",
                    status=\"success\"
                )
                supabase.table('telegram_actions').insert(action_record.dict()).execute()
                
                return {\"success\": True, \"action\": \"declined\"}
            else:
                await telegram_service.answer_callback_query(
                    callback_query_id,
                    f\"❌ Failed to decline: {decline_result.get('error', 'Unknown error')}\"
                )
                return {\"success\": False, \"error\": decline_result.get('error')}
        
        return {\"success\": True}
    
    except Exception as e:
        logger.error(f\"Error in telegram_webhook: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== GITLAB ACTION ROUTES ====================

@api_router.post(\"/gitlab/approve\")
async def gitlab_approve(request: GitLabActionRequest):
    \"\"\"Approve a GitLab merge request\"\"\"
    try:
        gitlab_service = get_gitlab_service()
        result = await gitlab_service.approve_merge_request(request.mr_url, request.gitlab_token)
        
        if result['success']:
            return {\"success\": True, \"message\": \"Merge request approved\", \"data\": result.get('data')}
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to approve'))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f\"Error in gitlab_approve: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post(\"/gitlab/merge\")
async def gitlab_merge(request: GitLabActionRequest):
    \"\"\"Merge a GitLab merge request\"\"\"
    try:
        gitlab_service = get_gitlab_service()
        result = await gitlab_service.merge_merge_request(request.mr_url, request.gitlab_token)
        
        if result['success']:
            return {\"success\": True, \"message\": \"Merge request merged\", \"data\": result.get('data')}
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to merge'))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f\"Error in gitlab_merge: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post(\"/gitlab/decline\")
async def gitlab_decline(request: GitLabActionRequest):
    \"\"\"Close/decline a GitLab merge request\"\"\"
    try:
        gitlab_service = get_gitlab_service()
        result = await gitlab_service.decline_merge_request(request.mr_url, request.gitlab_token)
        
        if result['success']:
            return {\"success\": True, \"message\": \"Merge request declined\", \"data\": result.get('data')}
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to decline'))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f\"Error in gitlab_decline: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SETTINGS ROUTES ====================

@api_router.post(\"/settings/save\")
async def save_settings(request: SaveSettingsRequest):
    \"\"\"Save user settings to Supabase\"\"\"
    try:
        supabase = get_supabase()
        settings_dict = request.settings.dict()
        settings_dict['updated_at'] = datetime.utcnow().isoformat()
        
        # Check if settings already exist
        existing = supabase.table('settings').select('*').eq('user_id', settings_dict.get('user_id', 'default')).execute()
        
        if existing.data:
            # Update existing
            result = supabase.table('settings').update(settings_dict).eq('id', existing.data[0]['id']).execute()
        else:
            # Insert new
            result = supabase.table('settings').insert(settings_dict).execute()
        
        logger.info(f\"Saved settings to Supabase\")
        return {\"success\": True, \"data\": result.data}
    
    except Exception as e:
        logger.error(f\"Failed to save settings: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get(\"/settings/get\")
async def get_settings(user_id: str = \"default\"):
    \"\"\"Get user settings from Supabase\"\"\"
    try:
        supabase = get_supabase()
        result = supabase.table('settings').select('*').eq('user_id', user_id).execute()
        
        if result.data:
            return {\"success\": True, \"settings\": result.data[0]}
        else:
            return {\"success\": True, \"settings\": None}
    
    except Exception as e:
        logger.error(f\"Failed to get settings: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=[\"*\"],
    allow_headers=[\"*\"],
)

@app.on_event(\"shutdown\")
async def shutdown_db_client():
    client.close()"
Observation: Edit was successful.
