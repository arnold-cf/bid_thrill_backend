import pika, json, time, math
from main import mysql, app
from services.rabbitmq import connect_to_rabbitmq
from api.payload.payload import Localtime
from datetime import datetime, timedelta, timezone
# from modules.auction_module.auction_controller import AuctionEngines
from modules.payments_module.payments_controller import Payments

def publish_task(queue_name, task_data):
    """Publish a task to RabbitMQ."""
    connection, channel = connect_to_rabbitmq()
    channel.queue_declare(queue=queue_name, durable=True)

    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(task_data),  # JSON serialization
        properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
    )
    connection.close()
    
    
def estimate_initial_close_time_minutes(total_bids_required, max_minutes=360):
    """ Estimate initial auction duration (minutes) from bids_required.
    - Scales expected bpm with size of auction
    - Clamps result to [120, max_minutes]
    """
    # Tune these once per product line if needed
    min_bpm, max_bpm = 1.0, 12.0     # bounds on expected bids/min
    bmin, bmax = 150, 4000           # expected min/max bid loads

    # normalize bids_required to [0..1]
    r = (total_bids_required - bmin) / (bmax - bmin)
    r = max(0.0, min(1.0, r))

    # higher bids_required -> lower bpm
    expected_bpm = max_bpm - r * (max_bpm - min_bpm)

    projected = total_bids_required / max(expected_bpm, 0.0001)
    return int(max(120, min(projected, max_minutes)))

def fetch_item_one_bids():
    """Fetch Item one bids"""
    
    try:
        cur = mysql.get_db().cursor()
        
        cur.execute("""SELECT id, ticket_number, amount, mobile_number FROM item_one_bids WHERE status = 0 ORDER BY id ASC LIMIT 100""")
        results = cur.fetchall()

        if results:
            for result in results:
                bid_id = result['id']
                ticket_number = result['ticket_number']
                amount = float(result['amount'])
                mobile_number = result['mobile_number']
                
                cur.execute("""UPDATE item_one_bids SET status = 2 WHERE id = %s""", (bid_id,))
                mysql.get_db().commit()
                
                cur.execute("""SELECT id FROM item_one_auctions WHERE status = 1 AND LIMIT 1""")
                active_auction = cur.fetchone()
                auction_id = active_auction["id"]
                
                send_stk_push = {
                                "auction_id":auction_id,
                                "ticket_number":ticket_number,
                                "amount":amount,
                                "mobile_number":mobile_number
                        }
                
                Payments().gg_pesa_paybill_stk(send_stk_push)

    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
            
def fetch_item_two_bids():
    """Fetch Item two bids"""
    
    try:
        cur = mysql.get_db().cursor()
        
        cur.execute("""SELECT id, ticket_number, amount, mobile_number FROM item_two_bids WHERE status = 0 ORDER BY id ASC LIMIT 100""")
        results = cur.fetchall()

        if results:
            for result in results:
                bid_id = result['id']
                ticket_number = result['ticket_number']
                amount = float(result['amount'])
                mobile_number = result['mobile_number']
                
                cur.execute("""UPDATE item_two_bids SET status = 2 WHERE id = %s""", (bid_id,))
                mysql.get_db().commit()
                
                cur.execute("""SELECT id FROM item_two_auctions WHERE status = 1 AND LIMIT 1""")
                active_auction = cur.fetchone()
                auction_id = active_auction["id"]
                
                send_stk_push = {
                                "auction_id":auction_id,
                                "ticket_number":ticket_number,
                                "amount":amount,
                                "mobile_number":mobile_number
                        }
                
                Payments().gg_pesa_paybill_stk(send_stk_push)

    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
        
def fetch_item_three_bids():
    """Fetch Item three bids"""
    
    try:
        cur = mysql.get_db().cursor()
        
        cur.execute("""SELECT id, ticket_number, amount, mobile_number FROM item_three_bids WHERE status = 0 ORDER BY id ASC LIMIT 100""")
        results = cur.fetchall()

        if results:
            for result in results:
                bid_id = result['id']
                ticket_number = result['ticket_number']
                amount = float(result['amount'])
                mobile_number = result['mobile_number']
                
                cur.execute("""UPDATE item_three_bids SET status = 2 WHERE id = %s""", (bid_id,))
                mysql.get_db().commit()
                
                cur.execute("""SELECT id FROM item_three_auctions WHERE status = 1 AND LIMIT 1""")
                active_auction = cur.fetchone()
                auction_id = active_auction["id"]
                
                send_stk_push = {
                                "auction_id":auction_id,
                                "ticket_number":ticket_number,
                                "amount":amount,
                                "mobile_number":mobile_number
                        }
                
                Payments().gg_pesa_paybill_stk(send_stk_push)

    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
        
def fetch_item_four_bids():
    """Fetch Item four bids"""
    
    try:
        cur = mysql.get_db().cursor()
        
        cur.execute("""SELECT id, ticket_number, amount, mobile_number FROM item_four_bids WHERE status = 0 ORDER BY id ASC LIMIT 100""")
        results = cur.fetchall()

        if results:
            for result in results:
                bid_id = result['id']
                ticket_number = result['ticket_number']
                amount = float(result['amount'])
                mobile_number = result['mobile_number']
                
                cur.execute("""UPDATE item_four_bids SET status = 2 WHERE id = %s""", (bid_id,))
                mysql.get_db().commit()
                
                cur.execute("""SELECT id FROM item_four_auctions WHERE status = 1 AND LIMIT 1""")
                active_auction = cur.fetchone()
                auction_id = active_auction["id"]
                
                send_stk_push = {
                                "auction_id":auction_id,
                                "ticket_number":ticket_number,
                                "amount":amount,
                                "mobile_number":mobile_number
                        }
                
                Payments().gg_pesa_paybill_stk(send_stk_push)

    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
        
def fetch_item_five_bids():
    """Fetch Item five bids"""
    
    try:
        cur = mysql.get_db().cursor()
        
        cur.execute("""SELECT id, ticket_number, amount, mobile_number FROM item_five_bids WHERE status = 0 ORDER BY id ASC LIMIT 100""")
        results = cur.fetchall()

        if results:
            for result in results:
                bid_id = result['id']
                ticket_number = result['ticket_number']
                amount = float(result['amount'])
                mobile_number = result['mobile_number']
                
                cur.execute("""UPDATE item_five_bids SET status = 2 WHERE id = %s""", (bid_id,))
                mysql.get_db().commit()
                
                cur.execute("""SELECT id FROM item_five_auctions WHERE status = 1 AND LIMIT 1""")
                active_auction = cur.fetchone()
                auction_id = active_auction["id"]
                
                send_stk_push = {
                                "auction_id":auction_id,
                                "ticket_number":ticket_number,
                                "amount":amount,
                                "mobile_number":mobile_number
                        }
                
                Payments().gg_pesa_paybill_stk(send_stk_push)

    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
        

def post_close_create_item_one_auction():
    """Close just ended auctions and create new Item One Auction"""
    
    try:
        cur = mysql.get_db().cursor()
        
        timenow_str = Localtime().gettime()
        cur.execute("""SELECT id FROM item_one_auctions WHERE status = 1 AND end_date < %s ORDER BY id ASC LIMIT 100""", (timenow_str,))
        results = cur.fetchall()

        if results:
            for result in results:
                auction_id = result['id']
                
                cur.execute("""UPDATE item_one_auctions SET status = 2 WHERE id = %s""", (auction_id,))
                mysql.get_db().commit()
                
                item_id = 1
                status = 1
                bids_required = 600
                #Allowed duration: Between 2–6 hours
                start_date = Localtime().gettime()
                
                start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                
                duration_mins = estimate_initial_close_time_minutes(bids_required, max_minutes=180)
                end_dt = start_dt + timedelta(minutes=duration_mins)
                end_date = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            
                cur.execute("""INSERT INTO item_one_auctions (item_id, start_date, end_date, status) VALUES (%s, %s, %s, %s)""", 
                                                             (item_id, start_date, end_date, status))
                mysql.get_db().commit()
                
    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
        
    
    

def post_close_create_item_two_auction():
    """Close just ended auctions and create new Item Two Auction"""
    
    try:
        cur = mysql.get_db().cursor()
        
        timenow_str = Localtime().gettime()
        cur.execute("""SELECT id FROM item_two_auctions WHERE status = 1 AND end_date < %s ORDER BY id ASC LIMIT 100""", (timenow_str,))
        results = cur.fetchall()

        if results:
            for result in results:
                auction_id = result['id']
                
                cur.execute("""UPDATE item_two_auctions SET status = 2 WHERE id = %s""", (auction_id,))
                mysql.get_db().commit()
                
                item_id = 1
                status = 1
                bids_required = 600
                #Allowed duration: Between 2–6 hours
                start_date = Localtime().gettime()
                
                start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                
                duration_mins = estimate_initial_close_time_minutes(bids_required, max_minutes=210)
                end_dt = start_dt + timedelta(minutes=duration_mins)
                end_date = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            
                cur.execute("""INSERT INTO item_two_auctions (item_id, start_date, end_date, status) VALUES (%s, %s, %s, %s)""", 
                                                             (item_id, start_date, end_date, status))
                mysql.get_db().commit()
                
    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
        
        
def post_close_create_item_three_auction():
    """Close just ended auctions and create new Item Three Auction"""
    
    try:
        cur = mysql.get_db().cursor()
        
        timenow_str = Localtime().gettime()
        cur.execute("""SELECT id FROM item_three_auctions WHERE status = 1 AND end_date < %s ORDER BY id ASC LIMIT 100""", (timenow_str,))
        results = cur.fetchall()

        if results:
            for result in results:
                auction_id = result['id']
                
                cur.execute("""UPDATE item_three_auctions SET status = 2 WHERE id = %s""", (auction_id,))
                mysql.get_db().commit()
                
                item_id = 1
                status = 1
                bids_required = 900
                #Allowed duration: Between 2–6 hours
                start_date = Localtime().gettime()
                
                start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                
                duration_mins = estimate_initial_close_time_minutes(bids_required, max_minutes=240)
                end_dt = start_dt + timedelta(minutes=duration_mins)
                end_date = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            
                cur.execute("""INSERT INTO item_three_auctions (item_id, start_date, end_date, status) VALUES (%s, %s, %s, %s)""", 
                                                             (item_id, start_date, end_date, status))
                mysql.get_db().commit()
                
    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
        
    
def post_close_create_item_four_auction():
    """Close just ended auctions and create new Item four Auction"""
    
    try:
        cur = mysql.get_db().cursor()
        
        timenow_str = Localtime().gettime()
        cur.execute("""SELECT id FROM item_four_auctions WHERE status = 1 AND end_date < %s ORDER BY id ASC LIMIT 100""", (timenow_str,))
        results = cur.fetchall()

        if results:
            for result in results:
                auction_id = result['id']
                
                cur.execute("""UPDATE item_four_auctions SET status = 2 WHERE id = %s""", (auction_id,))
                mysql.get_db().commit()
                
                item_id = 1
                status = 1
                bids_required = 4000
                #Allowed duration: Between 2–6 hours
                start_date = Localtime().gettime()
                
                start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                
                duration_mins = estimate_initial_close_time_minutes(bids_required, max_minutes=720)
                end_dt = start_dt + timedelta(minutes=duration_mins)
                end_date = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            
                cur.execute("""INSERT INTO item_four_auctions (item_id, start_date, end_date, status) VALUES (%s, %s, %s, %s)""", 
                                                             (item_id, start_date, end_date, status))
                mysql.get_db().commit()
                
    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
        

def post_close_create_item_five_auction():
    """Close just ended auctions and create new Item five Auction"""
    
    try:
        cur = mysql.get_db().cursor()
        
        timenow_str = Localtime().gettime()
        cur.execute("""SELECT id FROM item_five_auctions WHERE status = 1 AND end_date < %s ORDER BY id ASC LIMIT 100""", (timenow_str,))
        results = cur.fetchall()

        if results:
            for result in results:
                auction_id = result['id']
                
                cur.execute("""UPDATE item_five_auctions SET status = 2 WHERE id = %s""", (auction_id,))
                mysql.get_db().commit()
                
                item_id = 1
                status = 1
                bids_required = 172
                #Allowed duration: Between 2–6 hours
                start_date = Localtime().gettime()
                
                start_dt = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
                
                duration_mins = estimate_initial_close_time_minutes(bids_required, max_minutes=120)
                end_dt = start_dt + timedelta(minutes=duration_mins)
                end_date = end_dt.strftime("%Y-%m-%d %H:%M:%S")
            
                cur.execute("""INSERT INTO item_five_auctions (item_id, start_date, end_date, status) VALUES (%s, %s, %s, %s)""", 
                                                              (item_id, start_date, end_date, status))
                mysql.get_db().commit()
                
    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()