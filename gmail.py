import os
import pickle
import base64
import re
import time
import datetime
import google.auth
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Path to the JSON file containing your credentials
creds_file = ''  # Enter creds file location

# Path to store the token.pickle file (it will be created if it doesn't exist)
token_file = ''  # Enter creds file location


# email variables
specific_user_email = ''  # Enter target email
sender_email = ''  # Enter sender email
receiver_email = ''  # Enter receiver email


def authenticate():
    creds = None
    if os.path.exists(token_file):
        # Load saved credentials from token.pickle file
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh the credentials if expired
            creds.refresh(Request())
        else:
            # Run the authorization flow if no valid credentials are found
            flow = InstalledAppFlow.from_client_secrets_file(creds_file,
                                                             scopes=['https://www.googleapis.com/auth/gmail.readonly',
                                                                     'https://www.googleapis.com/auth/gmail.modify'])
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    return creds


def search_emails(service, query):
    try:
        # Execute the Gmail API search query
        response = service.users().messages().list(userId='me', q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])
        # Paginate through the results if there are more pages
        while 'nextPageToken' in response:
            time.sleep(1)  # Add a delay to avoid hitting rate limits
            page_token = response['nextPageToken']
            response = service.users().messages().list(
                userId='me', q=query, pageToken=page_token).execute()
            if 'messages' in response:
                messages.extend(response['messages'])
        return messages
    except googleapiclient.errors.HttpError as error:
        print(f"An error occurred: {error}")


def get_email(service, message_id):
    try:
        # Retrieve the full content of a specific email by its ID
        message = service.users().messages().get(
            userId='me', id=message_id, format='full').execute()
        return message
    except googleapiclient.errors.HttpError as error:
        print(f"An error occurred: {error}")


def main():
    current_hour = datetime.datetime.now().hour
    if current_hour >= 9 or current_hour >= 11:
        # Authenticate with the Gmail API
        creds = authenticate()
        service = googleapiclient.discovery.build(
            'gmail', 'v1', credentials=creds)

        # Define the search query
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.datetime.now() +
                    datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        query = f'from:{sender_email} after:{today} before:{tomorrow}'
        print(f"Search query: {query}")  # Debug print

        # Search for emails
        messages = search_emails(service, query)
        print(f"Number of messages found: {len(messages)}")  # Debug print
        # Iterate through the found emails
        for message in messages:
            # Get the full content of the email
            email = get_email(service, message['id'])

            # Extract the "From" header value
            from_header = None
            for header in email['payload']['headers']:
                if header['name'].lower() == 'from':
                    from_header = header['value']
                    break

            # Check if the "From" header value matches the sender_email
            if from_header != sender_email:
                continue

            # Extract the subject and the body of the email
            subject = email['payload']['headers'][0]['value']
            body = email['snippet']

            # Check if the subject contains the keyword
            if re.search('Python', subject, re.IGNORECASE):
                # Send the email notification
                send_email_notification(subject, body)
                print(f"Subject: {subject}")
                print(f"Body: {body}")
                print()
