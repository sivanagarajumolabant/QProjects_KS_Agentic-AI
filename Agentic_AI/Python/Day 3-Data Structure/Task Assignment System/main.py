from Service.task_service import Task_Service
from Service.user_service import User_Service


def main():
    task_service = Task_Service()
    user_Service = User_Service()

    user_Service.add_user(123,"mayank","mayank@isawesome.com")

    task_service.create_task(1,"Teach Data Structure basic","Teach from scratch")
    task_service.create_task(2,"Teach Advance Data Structure","teach from scratch")
    task_service.create_task(3,"Do a project","teach from scratch")
    task_service.create_task(4,"Take order from AK official","fix the error")


    print(task_service.complete_task())

    print(task_service.complete_task())
    print(task_service.complete_task())
    print(task_service.complete_task())

    history = task_service.get_task_history()
    
    print("History")
    print((history.pop().title))

    print((history.pop().title))
    print((history.pop().title))
    print((history.pop().title))



if __name__ == "__main__":
    main()