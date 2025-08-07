# Google OAuth Setup for Render Deployment

## Step 1: Configure Google OAuth for Render

### 1.1 Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Enable the **Google Identity API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**

### 1.2 OAuth Consent Screen
- Application name: `AI DocTransform`
- User support email: Your email
- Developer contact: Your email
- Authorized domains: Add `onrender.com`

### 1.3 OAuth 2.0 Client ID Configuration
**Application type**: Web application
**Name**: `AI DocTransform Render`

**Authorized JavaScript origins**:
```
https://ai-doctransform.onrender.com
```

**Authorized redirect URIs**:
```
https://ai-doctransform.onrender.com/auth/google/callback
https://ai-doctransform.onrender.com/
```

## Step 2: Configure Render Environment Variables

1. Go to your Render dashboard
2. Select your AI DocTransform service
3. Go to **Environment** tab
4. Add the following environment variables:

```bash
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

## Step 3: Update Your Templates

You need to replace `YOUR_GOOGLE_CLIENT_ID` in your templates with your actual Google Client ID.

**Option A: Use Environment Variable (Recommended)**
Update your Flask app to pass the Google Client ID to templates.

**Option B: Direct Replacement**
Replace `YOUR_GOOGLE_CLIENT_ID` in:
- `Crownix/templates/login.html`
- `Crownix/templates/signup.html`

## Step 4: Deploy to Render

1. Commit and push your changes:
```bash
git add .
git commit -m "Configure Google OAuth for Render deployment"
git push origin main
```

2. Render will automatically deploy your changes

## Step 5: Test the Integration

1. Visit: `https://ai-doctransform.onrender.com/login`
2. Click "Sign in with Google"
3. Complete the OAuth flow
4. Verify successful authentication

## Render-Specific Notes

### Environment Variables
- Set environment variables in Render dashboard, not in `.env` files
- Render automatically loads environment variables into your app
- Keep your Google Client Secret secure in Render's environment settings

### HTTPS
- Render provides HTTPS by default
- Google OAuth requires HTTPS for production
- Your Render URL: `https://ai-doctransform.onrender.com`

### Database Migration
Render will automatically run database migrations on deployment if you have:
```bash
# In your build command or start script
flask db upgrade
```

## Troubleshooting

### Common Render + Google OAuth Issues:

1. **"Redirect URI mismatch"**
   - Ensure your Render URL is exactly: `https://ai-doctransform.onrender.com`
   - Check that redirect URIs in Google Console match exactly

2. **"Client ID not found"**
   - Verify `GOOGLE_CLIENT_ID` environment variable is set in Render
   - Check that the Client ID is correctly passed to templates

3. **"Invalid client"**
   - Ensure your Google Client ID is active and not restricted
   - Check that your domain is authorized in Google Console

4. **Environment Variable Issues**
   - Environment variables in Render are case-sensitive
   - Restart your Render service after adding new environment variables

### Testing Checklist:
- [ ] Google Client ID added to Render environment variables
- [ ] Authorized origins include your Render URL
- [ ] Templates updated with correct Client ID
- [ ] HTTPS is working on your Render deployment
- [ ] Database migration completed successfully

## Security Best Practices for Render

1. **Never commit secrets**: Keep Google Client Secret in Render environment variables only
2. **Use HTTPS**: Render provides this automatically
3. **Monitor usage**: Check Google Cloud Console for OAuth usage
4. **Rotate credentials**: Regularly update your OAuth credentials

Your Google OAuth integration should now work perfectly with your Render deployment!
