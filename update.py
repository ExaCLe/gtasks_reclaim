from main import create_task, init
import pandas as pd


def main():
    service, reclaim_id = init()

    df = pd.read_csv('tasks.csv')
    tasks = service.tasks().list(tasklist=reclaim_id, maxResults=100).execute()
    for index, row in df.iterrows():
        title = row.title
        for task in tasks['items']:
            if task['title'] == "Rec: " + title:
                print(task)


if __name__ == "__main__":
    main()