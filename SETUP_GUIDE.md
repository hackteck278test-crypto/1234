Great! Now let me create a comprehensive setup guide for the user:
Action: file_editor create /app/SETUP_GUIDE.md --file-text "# Setup Guide - Telegram & Supabase Integration

## 🚀 Quick Start

Your GitLab MR Review app now has Telegram notifications with approve/decline buttons! Follow these steps to complete the setup.

## ✅ What's Already Done

- ✅ Backend API with Telegram and GitLab integration
- ✅ Frontend updates with token scope instructions
- ✅ Telegram bot configured (token and chat ID in place)
- ✅ Supabase credentials configured
- ✅ All code deployed and running

## 📋 Required Setup Steps

### Step 1: Create Supabase Database Tables (REQUIRED)

**This is the only required step to make everything work!**

1. Go to your Supabase project: https://uzwdtbwtjeduxzuibxdk.supabase.co

2. Navigate to: **SQL Editor** (left sidebar)

3. Click **\"New query\"**

4. Copy the entire contents of `/app/backend/supabase_schema.sql` and paste into the query editor

5. Click **\"Run\"** or press `Ctrl+Enter`

6. You should see: \"Success. No rows returned\"

This creates 3 tables:
- `reviews` - Stores all MR review data
- `settings` - Stores user preferences and tokens  
- `telegram_actions` - Logs approve/decline actions

**Verification:**
- Go to **Table Editor** in Supabase
- You should see 3 new tables: reviews, settings, telegram_actions

### Step 2: Configure GitLab Token (REQUIRED for Approve/Merge)

Your GitLab Personal Access Token must have these scopes:

1. Go to: **GitLab → User Settings → Access Tokens**

2. Click **\"Add new token\"**

3. Set name: \"MR Review Bot\"

4. Select these scopes:
   - ✅ `api` - Full API access (required for approve/merge)
   - ✅ `read_repository` - Read repository content
   - ✅ `write_repository` - Write access (required for merge)

5. Click **\"Create personal access token\"**

6. **Copy the token immediately** (you won't see it again!)

7. Go to your app → **Settings** page → **Integrations** tab

8. Paste token in **GitLab Integration** section

9. Click **\"Verify & Save\"**

### Step 3: Test the Integration

1. Go to **Merge Review** page

2. Enter a GitLab MR URL or select from open MRs

3. Click **\"Start Review\"**

4. Check your Telegram group for the notification with buttons!

5. Try clicking **\"Approve & Merge\"** or **\"Decline\"** button

## 🔧 Optional: Set Up Telegram Webhook (Production Only)

For local development, the bot works through polling. For production deployment, set up a webhook:

1. Get your production backend URL (e.g., from deployment)

2. Run this command (replace YOUR_BACKEND_URL):
```bash
curl -X POST \"https://api.telegram.org/bot8431621264:AAGgo6QIbzrFndSbvLEgn0jM9YCibTldq-4/setWebhook\" \
  -H \"Content-Type: application/json\" \
  -d '{\"url\": \"YOUR_BACKEND_URL/api/telegram/webhook\"}'
```

3. Verify webhook is set:
```bash
curl \"https://api.telegram.org/bot8431621264:AAGgo6QIbzrFndSbvLEgn0jM9YCibTldq-4/getWebhookInfo\"
```

## 📱 How It Works

### Review Flow:
1. User reviews an MR (manual or auto-review)
2. Review data saved to Supabase database
3. Comprehensive notification sent to Telegram with:
   - All issues (errors, warnings, info)
   - Summary and statistics
   - Approve & Decline buttons
   - MR link

### Button Actions:
1. User clicks button in Telegram
2. Telegram sends callback to backend
3. Backend retrieves review + GitLab token from Supabase
4. Backend executes GitLab API action:
   - **Approve**: Approves + merges the MR
   - **Decline**: Closes the MR
5. Action logged in `telegram_actions` table
6. Confirmation sent to user

## 🎯 Features

### ✅ Automatic Review Saving
- Every review is automatically saved to Supabase
- Full history available in database
- No data loss

### ✅ Complete Issue Reporting
- All errors, warnings, and info displayed
- Each issue includes:
  - File and line number
  - Rule violated
  - Description
  - Fix suggestion (if available)

### ✅ One-Click Actions
- Approve and merge in one click
- Decline/close with one click
- No need to visit GitLab

### ✅ Action Tracking
- All actions logged with timestamp
- Success/failure status recorded
- Full audit trail

## 🔍 Troubleshooting

### Telegram Notification Not Sent

**Symptoms:**
- Review completes but no Telegram message
- Error in backend logs about Telegram

**Solutions:**
1. Check bot token is correct in `/app/backend/.env`
2. Verify bot is member of Telegram group
3. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`

### Approve/Merge Button Doesn't Work

**Symptoms:**
- Click button but nothing happens
- Error message in Telegram

**Solutions:**
1. Verify GitLab token has `api`, `read_repository`, `write_repository` scopes
2. Check token is saved in Settings
3. Ensure MR is not already merged or closed
4. Check for merge conflicts in GitLab

### \"Supabase Error\" Messages

**Symptoms:**
- Can't save reviews
- Can't load history
- \"column does not exist\" errors

**Solution:**
- **Run the Supabase SQL script** (Step 1 above)
- Verify tables are created in Table Editor

### \"Invalid Token\" Error

**Symptoms:**
- GitLab actions fail
- \"401 Unauthorized\" errors

**Solutions:**
1. Regenerate token with correct scopes
2. Save new token in Settings
3. Verify token hasn't expired

## 📊 Database Schema

### `reviews` Table
```sql
- id (TEXT) - Unique review ID
- mr_url (TEXT) - Full MR URL
- mr_title (TEXT) - MR title
- author (TEXT) - MR author
- files_changed (INT) - Number of files
- lines_added (INT) - Lines added
- lines_removed (INT) - Lines removed
- review_time (TEXT) - Review duration
- status (TEXT) - passed/warnings/failed
- issues (JSONB) - Array of issue objects
- summary (TEXT) - Review summary
- reviewed_at (TIMESTAMP) - Review timestamp
- gitlab_token (TEXT) - Encrypted token
- project_id (TEXT) - GitLab project ID
- merge_request_iid (INT) - MR number
```

### `settings` Table
```sql
- id (TEXT) - Unique settings ID
- user_id (TEXT) - User identifier
- github_token (TEXT) - GitHub PAT
- gitlab_token (TEXT) - GitLab PAT
- telegram_enabled (BOOL) - Telegram toggle
- email_enabled (BOOL) - Email toggle
- auto_review_enabled (BOOL) - Auto-review toggle
- created_at (TIMESTAMP) - Creation time
- updated_at (TIMESTAMP) - Last update
```

### `telegram_actions` Table
```sql
- id (TEXT) - Unique action ID
- review_id (TEXT) - Linked review
- mr_url (TEXT) - MR URL
- action (TEXT) - approve/decline
- user_id (TEXT) - User who clicked
- created_at (TIMESTAMP) - Action time
- status (TEXT) - pending/success/failed
- error_message (TEXT) - Error if failed
```

## 🎨 Settings Page Features

Navigate to **Settings** to see:

### Integrations Tab
- GitLab token configuration
- Token scope requirements clearly listed
- Token verification before save
- GitHub integration (existing)

### Notifications Tab
- Telegram configuration status
- How buttons work explanation
- Notification preferences

## 🧪 Testing Commands

Test backend APIs locally:

### Test Health Check
```bash
curl http://localhost:8001/api/
```

### Test GitLab Approve (with your token)
```bash
curl -X POST http://localhost:8001/api/gitlab/approve \
  -H \"Content-Type: application/json\" \
  -d '{
    \"mr_url\": \"https://gitlab.com/owner/project/-/merge_requests/123\",
    \"gitlab_token\": \"your-token-here\"
  }'
```

### Test Telegram Notification (will actually send)
```bash
curl -X POST http://localhost:8001/api/telegram/send-notification \
  -H \"Content-Type: application/json\" \
  -d @test_review.json
```

Where `test_review.json` contains sample review data (see TELEGRAM_INTEGRATION.md).

## 📚 Additional Documentation

- `/app/TELEGRAM_INTEGRATION.md` - Detailed technical documentation
- `/app/backend/supabase_schema.sql` - Database schema
- Frontend .env: `/app/frontend/.env`
- Backend .env: `/app/backend/.env`

## 🆘 Need Help?

1. Check logs:
   - Backend: `tail -f /var/log/supervisor/backend.err.log`
   - Frontend: `tail -f /var/log/supervisor/frontend.err.log`

2. Verify services:
   ```bash
   sudo supervisorctl status
   ```

3. Restart services if needed:
   ```bash
   sudo supervisorctl restart backend
   sudo supervisorctl restart frontend
   ```

## ✨ You're All Set!

After completing Step 1 (Supabase tables) and Step 2 (GitLab token), your app is ready to:
- ✅ Send detailed Telegram notifications
- ✅ Approve and merge MRs from Telegram
- ✅ Decline/close MRs from Telegram
- ✅ Track all actions in database
- ✅ Maintain full review history

Enjoy your automated MR reviews! 🚀
"
Observation: Create successful: /app/SETUP_GUIDE.md
