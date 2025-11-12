import asyncio
from services.tasks import (
    fetch_item_one_bids,
    fetch_item_two_bids,
    fetch_item_three_bids,
    fetch_item_four_bids,
    fetch_item_five_bids,
    post_close_create_item_one_auction,
    post_close_create_item_two_auction,
    post_close_create_item_three_auction,
    post_close_create_item_four_auction,
    post_close_create_item_five_auction,
    
)
from services.rabbitmq import connect_to_rabbitmq
from main import app  # Import the Flask app

# Task handler mapping
TASK_HANDLERS = {
    "fetch_item_one_bids": fetch_item_one_bids,
    "fetch_item_two_bids": fetch_item_two_bids,
    "fetch_item_three_bids": fetch_item_three_bids,
    "fetch_item_four_bids": fetch_item_four_bids,
    "fetch_item_five_bids": fetch_item_five_bids,
    "post_close_create_item_one_auction": post_close_create_item_one_auction,
    "post_close_create_item_two_auction": post_close_create_item_two_auction,
    "post_close_create_item_three_auction": post_close_create_item_three_auction,
    "post_close_create_item_four_auction": post_close_create_item_four_auction,
    "post_close_create_item_five_auction": post_close_create_item_five_auction,
    
}

async def async_handle_task(ch, method, properties, body):
    """Handle RabbitMQ tasks asynchronously."""
    try:
        task_data = eval(body.decode())
        task_name = task_data.get("task")
        print(f"Processing task: {task_name}")

        # Push Flask app context for the duration of the task
        with app.app_context():
            if task_name in TASK_HANDLERS:
                print(f"Executing task: {task_name}")
                await asyncio.to_thread(TASK_HANDLERS[task_name])
            else:
                print(f"Unknown task received: {task_name}")

        # Acknowledge the message after successful processing
        print(f"Task '{task_name}' completed successfully.")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error processing task: {e}")
        # Optionally, reject the message if processing fails
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def start_worker():
    """Start RabbitMQ worker."""
    connection, channel = connect_to_rabbitmq()

    # Define the task queues
    task_queues = [
        "fetch_item_one_bids",
        "fetch_item_two_bids",
        "fetch_item_three_bids",
        "fetch_item_four_bids",
        "fetch_item_five_bids",
        "post_close_create_item_one_auction",
        "post_close_create_item_two_auction",
        "post_close_create_item_three_auction",
        "post_close_create_item_four_auction",
        "post_close_create_item_five_auction",
        
    ]

    # Declare all task queues
    for queue in task_queues:
        channel.queue_declare(queue=queue, durable=True)

    # Consume messages from all queues dynamically
    for queue in task_queues:
        channel.basic_qos(prefetch_count=1)  # Process one message at a time
        channel.basic_consume(
            queue=queue,
            on_message_callback=lambda ch, method, properties, body: asyncio.run(
                async_handle_task(ch, method, properties, body)
            ),
        )

    print("Worker is running... Press Ctrl+C to stop.")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Worker stopped by user.")
        connection.close()
