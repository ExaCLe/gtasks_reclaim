from main import init


def main():
    service, reclaim_id = init()

    # Delete all the Recurring Tasks
    found_new = True
    while found_new:
        found_new = False
        for task in service.tasks().list(tasklist=reclaim_id, maxResults=100).execute()['items']:
            if "Rec: " in task['title']:
                found_new = True
                service.tasks().delete(tasklist=reclaim_id, task=task['id']).execute()
                print("Deleted: " + task['title'])


if __name__ == "__main__":
    main()