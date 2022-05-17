from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
import datetime
import os
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pandas as pd


SCOPES = ['https://www.googleapis.com/auth/tasks']
WEEKS_TO_PLAN_AHEAD = 3


def main():
    service, reclaim_id = init()

    # Get the data from the .csv file for processing
    df = pd.read_csv('tasks.csv')
    df.next_due = pd.to_datetime(df.next_due)
    df.notbefore = pd.to_datetime(df.notbefore)

    end_of_vision_date = datetime.datetime.now() + datetime.timedelta(days=WEEKS_TO_PLAN_AHEAD*7)
    print("Inserting tasks...")

    # Schedule the new tasks
    for index, row in df.iterrows():
        if row.next_due > end_of_vision_date:
            continue
        else:
            while row.next_due <= end_of_vision_date:
                create_task(service,
                            reclaim_id,
                            row.title,
                            convert_to_rfc_datetime(row.next_due.year, row.next_due.month, row.next_due.day),
                            notbefore=row.notbefore,
                            duration=row.duration)
                if not pd.isna(row.notbefore):
                    row.notbefore += datetime.timedelta(days=row.frequency)
                row.next_due += datetime.timedelta(days=row.frequency)

            # Change the date in the real df
            df.iloc[index, df.columns.get_loc('next_due')] = row.next_due
            if not pd.isna(row.notbefore):
                df.iloc[index, df.columns.get_loc('notbefore')] = row.notbefore
    print("Done... Saving to .csv")
    # save the changes in the .csv file
    df.to_csv('tasks.csv', index=False)


def init():
    print("Connecting to Google Tasks...")
    # create the credentials
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('tasks', 'v1', credentials=creds)

        # Call the Tasks API
        results = service.tasklists().list().execute()
        items = results.get('items', [])

        if not items:
            print('No task lists found.')
            return

        reclaim_id = None
        for item in items:
            if 'Reclaim' in item['title']:
                reclaim_id = item['id']
        return service, reclaim_id

    except HttpError as err:
        print(err)
        return None, None


def convert_to_rfc_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    dt = datetime.datetime(year, month, day, hour, minute, 0, 000).isoformat() + 'Z'
    return dt


def create_task(service, tasklist_id, task_title, task_due, notbefore=None, duration=None):
    if notbefore is not None or duration is not None:
        if notbefore is None:
            task_title = f"{task_title} (duration:{duration})"
        elif duration is None:
            task_title = f"{task_title} (notbefore:{notbefore})"
        else:
            task_title = f"{task_title} (notbefore:{notbefore} duration:{duration})"
    task = {
        'title': "Rec: " + task_title,
        'due': task_due
    }
    print(f"Creating task: {task_title} with due date: {task_due}")
    return service.tasks().insert(tasklist=tasklist_id, body=task).execute()


if __name__ == '__main__':
    main()


