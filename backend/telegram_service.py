"import os
import logging
from typing import List, Dict, Any
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from models import ReviewData, ReviewIssue
import json

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("Telegram credentials not configured")
        
        self.bot = Bot(token=self.bot_token)


     def _escape_markdown(self, text: str) -> str:
        """Escape special characters for Markdown"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'{char}')
        return text
    
    def _format_review_message(self, review: ReviewData) -> str:
        """Format the review data into a comprehensive Telegram message"""
        
        # Status emoji
        status_emoji = {
            "passed": "✅",
            "warnings": "⚠️",
            "failed": "❌"
        }
       
        
        # Build message
        message_parts = [
             f"{status_emoji.get(review.status, '📝')} *Merge Request Review Complete*",
            f"",
            f"━━━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"📋 *Title:* {self._escape_markdown(review.mr_title)}",
            f"👤 *Author:* {self._escape_markdown(review.author)}",
            f"📊 *Status:* {review.status.upper()}",
            f"⏱ *Review Time:* {review.review_time}",
            f"",
            f"📈 *Changes:*",
            f"  • Files Changed: {review.files_changed}",
             f"  • Lines Added: +{review.lines_added}",
            f"  • Lines Removed: -{review.lines_removed}",
            f"",
            f"📝 *Summary:*",
            f"{review.summary}",
             f"{self._escape_markdown(review.summary)}",
            f"",
        ]
        
        # Add issues section
        if review.issues:
            message_parts.append(f"🔍 *Issues Found:* {len(review.issues)}
")
            message_parts.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
")
            
            # Group issues by severity
            errors = [i for i in review.issues if i.severity == "error"]
            warnings = [i for i in review.issues if i.severity == "warning"]
            infos = [i for i in review.issues if i.severity == "info"]
            
            if errors:
                message_parts.append(f"🔴 *ERRORS ({len(errors)}):*
")
                for idx, issue in enumerate(errors, 1):
                    message_parts.append(
                        f"{idx}. `{issue.file}:{issue.line}`
"
                        f"   Rule: {issue.rule}
"
                        f"   {issue.message}"
                    )
                    if issue.suggestion:
                        message_parts.append(f"    {issue.suggestion}")
                    message_parts.append("")
            
            if warnings:
                message_parts.append(f" *WARNINGS ({len(warnings)}):*
")
                for idx, issue in enumerate(warnings, 1):
                    message_parts.append(
                        f"{idx}. `{issue.file}:{issue.line}`
"
                        f"   Rule: {issue.rule}
"
                        f"   {issue.message}"
                    )
                    if issue.suggestion:
                        message_parts.append(f"    {issue.suggestion}")
                    message_parts.append("")
            
            if infos:
                message_parts.append(f" *INFO ({len(infos)}):*
")
                for idx, issue in enumerate(infos, 1):
                    message_parts.append(
                        f"{idx}. `{issue.file}:{issue.line}`
"
                        f"   Rule: {issue.rule}
"
                        f"   {issue.message}"
                    )
                    if issue.suggestion:
                        message_parts.append(f"    {issue.suggestion}")
                    message_parts.append("")
        else:
            message_parts.append(f"✨ *No Issues Found!*
")
        
        # Add MR link at the end
        message_parts.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        message_parts.append(f"🔗 *Merge Request:*")
        message_parts.append(f"{review.mr_url}")
        
        return "
".join(message_parts)
    
    def _create_inline_keyboard(self, review_id: str, mr_url: str) -> InlineKeyboardMarkup:
        """Create inline keyboard with Approve and Decline buttons"""
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Approve & Merge",
                    callback_data=json.dumps({
                        "action": "approve",
                        "review_id": review_id,
                        "mr_url": mr_url
                    })
                ),
                InlineKeyboardButton(
                    "❌ Decline",
                    callback_data=json.dumps({
                        "action": "decline",
                        "review_id": review_id,
                        "mr_url": mr_url
                    })
                )
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def send_review_notification(self, review: ReviewData) -> bool:
        """Send review notification to Telegram with approve/decline buttons"""
        try:
            message = self._format_review_message(review)
            keyboard = self._create_inline_keyboard(review.id, review.mr_url)
            
            # Split message if it's too long (Telegram limit is 4096 characters)
            if len(message) > 4000:
                # Send in chunks
                chunks = self._split_message(message, 4000)
                for i, chunk in enumerate(chunks):
                    if i == len(chunks) - 1:
                        # Add buttons to last chunk
                        await self.bot.send_message(
                            chat_id=self.chat_id,
                            text=chunk,
                            parse_mode="Markdown",
                            reply_markup=keyboard
                        )
                    else:
                        await self.bot.send_message(
                            chat_id=self.chat_id,
                            text=chunk,
                            parse_mode="Markdown"
                        )
            else:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            
            logger.info(f"Telegram notification sent for review {review.id}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram notification: {str(e)}")
            return False
    
    def _split_message(self, message: str, max_length: int) -> List[str]:
        """Split long message into chunks"""
        chunks = []
        current_chunk = ""
        
        for line in message.split("
"):
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + "
"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line + "
"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def answer_callback_query(self, callback_query_id: str, text: str):
        """Answer callback query to show notification to user"""
        try:
            await self.bot.answer_callback_query(
                callback_query_id=callback_query_id,
                text=text,
                show_alert=True
            )
        except TelegramError as e:
            logger.error(f"Failed to answer callback query: {str(e)}")
    
    async def edit_message(self, chat_id: str, message_id: int, text: str):
        """Edit existing message (to update button status)"""
        try:
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode="Markdown"
            )
        except TelegramError as e:
            logger.error(f"Failed to edit message: {str(e)}")


# Singleton instance
_telegram_service = None


def get_telegram_service() -> TelegramService:
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramService()
    return _telegram_service
"
