def format_task_list(tasks):
    return "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
