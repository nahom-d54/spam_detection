[x] It should get the folders dynamically so there should be a route to get the folders - Implemented: GET /emails/folders/list returns all email folders
[x] Then we query the folders results and when opened we score it and ask for confirmation to move to spam - Implemented: GET /emails/{email_id} automatically scores spam (returns is_spam and confidence) - Implemented: POST /emails/{email_id}/confirm-spam for user confirmation to move to spam folder - Frontend can show a button when is_spam=true with confidence score

## API Endpoints Summary:

- GET /emails/folders/list - Get all folders dynamically
- GET /emails/{email_id} - Get email details with spam detection (is_spam, confidence)
- POST /emails/{email_id}/confirm-spam - Confirm and move spam to spam folder
- POST /emails/{email_id}/move - General move endpoint for any folder
