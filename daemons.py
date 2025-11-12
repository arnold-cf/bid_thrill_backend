import sys
import asyncio
from services.tasks import publish_task
from services.worker import start_worker

# Define constants for task names
TASK_FETCH_GAMEONE_STAKING = "fetch_game_one_staking"
TASK_FETCH_GAMETWO_STAKING = "fetch_game_two_staking"
TASK_PROCESS_B2C_DISBURSEMENT = "process_b2c_disbursement"

# Sleep durations for each task (in seconds)
TASK_SLEEP_DURATIONS = {
    TASK_FETCH_GAMEONE_STAKING: 2,
    TASK_FETCH_GAMETWO_STAKING: 2,
    TASK_PROCESS_B2C_DISBURSEMENT: 2,
}

def main():
    """Main entry point for running daemon commands."""
    if len(sys.argv) < 2:
        print("Usage: python3 daemons.py [publish|worker|periodic_publish]")
        return

    command = sys.argv[1]

    if command == "publish":
        run_publish_tasks()
    elif command == "worker":
        run_worker()
    elif command == "periodic_publish":
        asyncio.run(run_periodic_publisher())  # Run the periodic publisher asynchronously
    else:
        print(f"Unknown command: {command}")
        print("Available commands: publish, worker, periodic_publish")

def run_publish_tasks():
    """Publish daily tasks to RabbitMQ."""
    print("Publishing daily tasks...")
    try:
        for task_name in TASK_SLEEP_DURATIONS.keys():
            publish_task(task_name, {"task": task_name})
        print("Tasks published successfully.")
    except Exception as e:
        print(f"Error publishing tasks: {e}")
        raise

def run_worker():
    """Start the worker to consume tasks."""
    print("Starting worker...")
    try:
        start_worker()
    except Exception as e:
        print(f"Error starting worker: {e}")
        raise

async def publish_task_async(task_name, payload, sleep_duration):
    """Asynchronous wrapper for publishing a task with a delay."""
    try:
        while True:
            print(f"Publishing task: {task_name}")
            await asyncio.to_thread(publish_task, task_name, payload)  # Publish the task in a non-blocking way
            print(f"Task '{task_name}' published. Sleeping for {sleep_duration} seconds...")
            await asyncio.sleep(sleep_duration)
    except Exception as e:
        print(f"Error publishing task '{task_name}': {e}")
        raise


async def run_periodic_publisher():
    """Start periodic publishers for each task based on their intervals."""
    print("Starting periodic publisher. Press Ctrl+C to stop.")
    try:
        # Create and schedule a periodic task for each defined task
        tasks = [
            asyncio.create_task(publish_task_async(task_name, {"task": task_name}, sleep_duration))
            for task_name, sleep_duration in TASK_SLEEP_DURATIONS.items()
        ]
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("Periodic publisher stopped gracefully.")
    except Exception as e:
        print(f"Unexpected error in periodic publisher: {e}")
        raise


if __name__ == "__main__":
    main()
