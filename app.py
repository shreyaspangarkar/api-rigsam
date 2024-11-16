from flask import Flask, jsonify, request, render_template
import mysql.connector
from mysql.connector import Error
import os

app = Flask(__name__)

# Database connection function
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'monsterzero'),
            password=os.getenv('DB_PASSWORD', 'Monsterzero@8910'),
            database=os.getenv('DB_NAME', 'full_db')
        )
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

# Define the API endpoint for fetching member details
@app.route('/api/fetch', methods=['GET'])
def fetch_member():
    member_id = request.args.get('member_id')
    if not member_id:
        return jsonify({"error": "member_id is required"}), 400

    query = """
    SELECT 
        member_name, 
        member_id, 
        present_add1, 
        off_pin,
        gaurdian_name,
        gaurdian_relation 
    FROM 
        mast_member 
    WHERE 
        member_id = %s;
    """

    connection = create_connection()
    
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(query, (member_id,))
        result = cursor.fetchone()  # Fetch a single result
        
        # Ensure to fetch remaining results if any
        while cursor.nextset():  # This will consume any remaining result sets
            pass
        
        if not result:
            return jsonify({"message": "No member found with this ID"}), 404
        
        return jsonify(result), 200
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        connection.close()

# Define the API endpoint for loans
@app.route('/loans', methods=['GET'])
def get_loans():
    surety_id = request.args.get('surety_id')
    if not surety_id:
        return jsonify({"error": "surety_id is required"}), 400

    query = """
    SELECT DISTINCT
        a.member_id,
        c.loan_id,
        c.start_date,
        c.dr_loan_amt,
        c.loan_due,
        e.stage_name,
        ROUND(IFNULL(c.arr_inst_amt, 0) + IFNULL(c.curr_inst_amt, 0) - IFNULL(c.cr_inst_amt, 0), 0) AS inst_amt,
        ROUND(IFNULL(c.arr_int_amt, 0) + IFNULL(c.curr_int_amt, 0), 0) AS int_amt,
        ROUND(IFNULL(c.arr_pnl_int_amt, 0) + IFNULL(c.curr_pnl_int_amt, 0) - IFNULL(c.cr_pnl_int_amt, 0), 0) AS pnl_int_amt,
        ROUND(IFNULL(c.arr_post_amt, 0) + IFNULL(c.dr_post_amt, 0) - IFNULL(c.cr_post_amt, 0), 0) AS post_amt,
        ROUND(IFNULL(c.arr_arb_amt, 0) + IFNULL(c.dr_arb_amt, 0) - IFNULL(c.cr_arb_amt, 0), 0) AS arb_amt,
        c.loan_due + ROUND(
            IFNULL(c.arr_int_amt, 0) + IFNULL(c.curr_int_amt, 0) +
            IFNULL(c.arr_pnl_int_amt, 0) + IFNULL(c.curr_pnl_int_amt, 0) - IFNULL(c.cr_pnl_int_amt, 0) +
            IFNULL(c.arr_post_amt, 0) + IFNULL(c.dr_post_amt, 0) - IFNULL(c.cr_post_amt, 0) +
            IFNULL(c.arr_arb_amt, 0) + IFNULL(c.dr_arb_amt, 0) - IFNULL(c.cr_arb_amt, 0), 0
        ) AS tot_amt,
        b.member_name,
        b.gaurdian_relation,
        b.gaurdian_name,
        b.present_add1,
        b.present_add2,
        b.present_area,
        b.pin 
    FROM 
        member_vs_surety_loan a
    JOIN 
        mast_member b ON a.member_id = b.member_id
    JOIN 
        mast_demand c ON a.member_id = c.member_id AND a.loan_id = c.loan_id AND a.start_date = c.start_date
    JOIN 
        mast_loan d ON a.member_id = d.member_id AND a.loan_id = d.loan_id AND a.start_date = d.start_date
    JOIN 
        mast_action_stage e ON d.action_stage = e.stage_id 
    WHERE 
        c.loan_due > 0 
        AND a.surety_id = %s;
    """

    connection = create_connection()
    
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(query, (surety_id,))
        results = cursor.fetchall()
        
        if not results:
            return jsonify({"message": "No loans found for this surety ID"}), 404
        
        return jsonify(results), 200
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        connection.close()

# Render the index page and handle form submission
@app.route('/', methods=['GET', 'POST'])
def home():
    loans_data = []
    
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        
        # Fetch loans using the member ID
        response = get_loans()  
        
        if response[1] == 200:  
            loans_data = response[0]  
        
    return render_template('index.html', loans=loans_data)

if __name__ == '__main__':
    app.run(debug=True)







