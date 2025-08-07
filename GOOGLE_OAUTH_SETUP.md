# Google OAuth Setup Guide

## Step 1: Create Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API or Google Identity API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Configure the OAuth consent screen:
   - Application name: "AI DocTransform"
   - User support email: your email
   - Developer contact: your email
6. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Name: "AI DocTransform Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:5000` (for development)
     - `https://ai-doctransform.onrender.com` (for production)
   - Authorized redirect URIs:
     - `http://localhost:5000/auth/google/callback` (for development)
     - `https://ai-doctransform.onrender.com/auth/google/callback` (for production)

## Step 2: Configure Environment Variables

Add the following to your `.env` file:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

## Step 3: Update Frontend Templates

Replace `YOUR_GOOGLE_CLIENT_ID` in the following files with your actual Google Client ID:

- `Crownix/templates/login.html` (line with `data-client_id`)
- `Crownix/templates/signup.html` (line with `data-client_id`)

## Step 4: Database Migration

Run the database migration to add Google OAuth fields:

```bash
# If using Flask-Migrate
flask db upgrade

# Or manually run the migration script
python migrations/add_google_oauth_fields.py
```

## Step 5: Test the Integration

1. Start your Flask application
2. Navigate to the login/signup page
3. Click "Sign in with Google" or "Sign up with Google"
4. Complete the Google OAuth flow
5. Verify that the user is created/logged in successfully

## Security Notes

- Keep your Google Client Secret secure and never commit it to version control
- Use HTTPS in production for OAuth callbacks
- Regularly rotate your OAuth credentials
- Monitor OAuth usage in Google Cloud Console

## Troubleshooting

### Common Issues:

1. **"Invalid client" error**: Check that your Client ID matches exactly
2. **"Redirect URI mismatch"**: Ensure your redirect URIs are configured correctly in Google Cloud Console
3. **"Access blocked"**: Make sure your OAuth consent screen is properly configured

### Testing in Development:

- Use `http://localhost:5000` as your origin
- Ensure your `.env` file is loaded properly
- Check browser console for JavaScript errors
