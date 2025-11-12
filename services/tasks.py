import pika, json, time, math
from main import mysql, app
from services.rabbitmq import connect_to_rabbitmq
from api.payload.payload import Localtime
from datetime import datetime, timedelta, timezone
from modules.game_module.game_controller import GameEngines
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

def fetch_game_one_staking():
    """Fetch game one staking"""
    
    try:
        cur = mysql.get_db().cursor()
        
        cur.execute("""SELECT id, session_id, game_option, box_selected, mobile_number FROM game_one_staking WHERE status = 0 ORDER BY id ASC LIMIT 100""")
        results = cur.fetchall()

        if results:
            for result in results:
                stake_id = result['id']
                session_id = result['session_id']
                game_option = result['game_option']
                box_selected = result['box_selected']
                mobile_number = result['mobile_number']
                
                cur.execute("""UPDATE game_one_staking SET status = 2 WHERE id = %s""", (stake_id))
                mysql.get_db().commit()
                
                params = {"game_option":game_option,
                          "box_selected":box_selected,
                          "mobile_number":mobile_number,
                          "session_id":session_id
                }
                
                GameEngines().game_one(params)

    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
            
def fetch_game_two_staking():
    """Fetch game two staking"""
    
    try:
        cur = mysql.get_db().cursor()
        
        cur.execute("""SELECT id, session_id, game_option, box_selected, mobile_number FROM game_two_staking WHERE status = 0 ORDER BY id ASC LIMIT 100""")
        results = cur.fetchall()

        if results:
            for result in results:
                stake_id = result['id']
                session_id = result['session_id']
                game_option = result['game_option']
                box_selected = result['box_selected']
                mobile_number = result['mobile_number']
                
                cur.execute("""UPDATE game_two_staking SET status = 2 WHERE id = %s""", (stake_id))
                mysql.get_db().commit()
                
                params = {"game_option":game_option,
                          "box_selected":box_selected,
                          "mobile_number":mobile_number,
                          "session_id":session_id
                }
                
                GameEngines().game_two(params)

    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()
        
def process_b2c_disbursement():
    """Process b2c disbursement"""
    
    try:
        cur = mysql.get_db().cursor()
        
        cur.execute("""SELECT id, msisdn, amount FROM mpesa_b2c_disbursement_requests WHERE status = 0 AND processed = 0 ORDER BY id ASC LIMIT 100""")
        results = cur.fetchall()

        if results:
            for result in results:
                request_id = result['id']
                mobile_number = result['msisdn']
                withdraw_amount = float(result['amount'])
                
                mobilenumber = ''.join(mobile_number.split()) 
                msisdn ='254' + mobilenumber[-9:] 
                
                amount = math.ceil(withdraw_amount)

                cur.execute("""UPDATE mpesa_b2c_disbursement_requests SET processed = 2 WHERE id = %s""", (request_id))
                mysql.get_db().commit()
                
                details = {
                "msisdn":msisdn,
                "amount":amount,
                "b2c_request_id":request_id
                }
                
                disburse_loan_amount = Payments().b2c_disbursement(details)

    except Exception as e:
        # Roll back the transaction in case of an error
        print(f"Error copying matches: {e}")
        mysql.get_db().rollback()