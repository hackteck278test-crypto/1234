Great! Frontend is running. Now let me create a comprehensive README with instructions for setting up the Supabase tables. Let me also create a document that explains the new features:
Action: file_editor create /app/TELEGRAM_INTEGRATION.md --file-text "# Telegram Bot Integration with GitLab Approve/Decline

## Overview
Your GitLab MR Review app now includes full Telegram integration with inline approve/decline buttons that directly interact with GitLab.

## Features Implemented

### 1. **Telegram Notifications**
- Comprehensive review notifications sent to your Telegram group
- Includes:
  - MR title, author, status
  - Files changed, lines added/removed
  - Complete list of all issues (errors, warnings, info)
  - Review summary
  - MR link at the end

### 2. **Interactive Buttons**
- **✅ Approve & Merge**: Approves and merges the MR directly in GitLab
- **❌ Decline**: Closes the MR in GitLab

### 3. **Supabase Database Integration**
- Stores all review data
- Tracks user settings
- Logs all approve/decline actions

## Configuration

### Telegram Bot
Already configured in your backend:
- **Bot Token**: `8431621264:AAGgo6QIbzrFndSbvLEgn0jM9YCibTldq-4`
- **Chat ID**: `-1003841579486`

### Supabase
Already configured:
- **Project URL**: `https://uzwdtbwtjeduxzuibxdk.supabase.co`
- **Anon Key**: Configured in backend `.env`

## Setup Instructions

### Step 1: Create Supabase Tables

Run the SQL script located at `/app/backend/supabase_schema.sql` in your Supabase SQL Editor:

1. Go to https://uzwdtbwtjeduxzuibxdk.supabase.co
2. Navigate to SQL Editor
3. Copy and paste the contents of `supabase_schema.sql`
4. Click \"Run\"

This will create three tables:
- `reviews` - Stores all MR review data
- `settings` - Stores user settings and tokens
- `telegram_actions` - Logs all approve/decline actions

### Step 2: Set Telegram Webhook (Optional)

If you want Telegram to send button clicks to your backend:

1. Set up a public URL for your backend (e.g., ngrok or deployment URL)
2. Register webhook with Telegram:
```bash
curl -X POST \"https://api.telegram.org/bot8431621264:AAGgo6QIbzrFndSbvLEgn0jM9YCibTldq-4/setWebhook\" \
  -H \"Content-Type: application/json\" \
  -d '{\"url\": \"YOUR_BACKEND_URL/api/telegram/webhook\"}'
```

**Note**: For local development, the buttons work through polling, but for production you should set up the webhook.

### Step 3: Configure GitLab Token

⚠️ **IMPORTANT**: Your GitLab token must have the following scopes:
- `api` - Full API access (required for approve/merge)
- `read_repository` - Read repository content
- `write_repository` - Write to repository (required for merge)

To create a token with these scopes:
1. Go to GitLab → User Settings → Access Tokens
2. Create a new token with the above scopes
3. Save the token in the app Settings page

## How It Works

### Review Flow:
1. User reviews an MR (manually or auto-review)
2. Review data is saved to Supabase
3. Telegram notification is sent with all details
4. Notification includes approve/decline buttons

### Button Click Flow:
1. User clicks \"Approve & Merge\" or \"Decline\" in Telegram
2. Telegram sends callback to backend webhook
3. Backend retrieves review data from Supabase
4. Backend uses GitLab token to execute action:
   - **Approve**: Calls GitLab API to approve then merge the MR
   - **Decline**: Calls GitLab API to close the MR
5. Action is logged in Supabase `telegram_actions` table
6. User receives confirmation in Telegram

## API Endpoints

### Backend Endpoints:

#### Save Review
```
POST /api/reviews/save
Body: {
  \"review_data\": { ... }
}
```

#### Get Review History
```
GET /api/reviews/history?limit=50
```

#### Send Telegram Notification
```
POST /api/telegram/send-notification
Body: ReviewData
```

#### Telegram Webhook
```
POST /api/telegram/webhook
Body: Telegram callback query
```

#### GitLab Actions
```
POST /api/gitlab/approve
POST /api/gitlab/merge
POST /api/gitlab/decline
Body: {
  \"mr_url\": \"https://gitlab.com/...\",
  \"gitlab_token\": \"glpat-xxx\"
}
```

#### Settings
```
POST /api/settings/save
GET /api/settings/get?user_id=default
```

## Troubleshooting

### Issue: Buttons don't work
**Solution**: Make sure you've set up the Telegram webhook or the app has access to receive button callbacks

### Issue: \"GitLab token not found\"
**Solution**: Configure your GitLab token in Settings with required scopes

### Issue: Approve/Merge fails
**Solutions**:
1. Verify token has `api` and `write_repository` scopes
2. Check if MR is already merged or closed
3. Check if there are conflicts or failing pipelines

### Issue: Telegram notification not sent
**Solutions**:
1. Verify bot token and chat ID in backend `.env`
2. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
3. Ensure bot is added to the Telegram group

## Testing

### Test Telegram Notification:
```bash
curl -X POST http://localhost:8001/api/telegram/send-notification \
  -H \"Content-Type: application/json\" \
  -d '{
    \"id\": \"test-123\",
    \"mr_url\": \"https://gitlab.com/test/repo/-/merge_requests/1\",
    \"mr_title\": \"Test MR\",
    \"author\": \"testuser\",
    \"files_changed\": 5,
    \"lines_added\": 100,
    \"lines_removed\": 50,
    \"review_time\": \"2.5s\",
    \"status\": \"warnings\",
    \"issues\": [
      {
        \"id\": \"1\",
        \"file\": \"test.py\",
        \"line\": 10,
        \"severity\": \"warning\",
        \"message\": \"Test warning\",
        \"rule\": \"test-rule\"
      }
    ],
    \"summary\": \"Test review summary\",
    \"reviewed_at\": \"2025-07-20T12:00:00Z\"
  }'
```

### Test GitLab Approve:
```bash
curl -X POST http://localhost:8001/api/gitlab/approve \
  -H \"Content-Type: application/json\" \
  -d '{
    \"mr_url\": \"https://gitlab.com/owner/project/-/merge_requests/123\",
    \"gitlab_token\": \"your-token-here\"
  }'
```

## Security Notes

- GitLab tokens are stored encrypted in Supabase
- Tokens are never exposed in Telegram messages
- All API endpoints validate tokens before executing actions
- Row Level Security (RLS) is enabled on all Supabase tables

## Auto-Review Feature

The existing auto-review feature remains unchanged:
- When you set GitLab/GitHub tokens in Settings
- The app automatically fetches open MRs
- The first MR is auto-reviewed
- Telegram notification is sent automatically

## Database Schema

### `reviews` Table
- Stores complete review data
- Includes MR details, issues, summary
- Links to GitLab token for approval actions

### `settings` Table
- Stores user preferences
- Includes saved tokens
- Notification preferences

### `telegram_actions` Table
- Logs all approve/decline actions
- Tracks success/failure status
- Links to review records

## Next Steps

1. ✅ Set up Supabase tables using the SQL script
2. ✅ Configure GitLab token with required scopes
3. ✅ Test a review and check Telegram notification
4. ✅ Test approve/decline buttons
5. ⚠️ (Optional) Set up webhook for production

Enjoy your automated MR reviews with Telegram integration! 🚀
"
Observation: Create successful: /app/TELEGRAM_INTEGRATION.md
