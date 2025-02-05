from flask import Flask, request, jsonify
import sqlite3
import re

app = Flask(__name__)

# Create or connect to an SQLite database
def get_db_connection():
    conn = sqlite3.connect("company.db")
    conn.row_factory = sqlite3.Row  # Enables column access by name
    return conn

# Create the Employees and Departments tables
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS Employees")
    cursor.execute("DROP TABLE IF EXISTS Departments")

    cursor.execute('''CREATE TABLE Employees (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL,
                        Department TEXT NOT NULL,
                        Salary REAL NOT NULL,
                        Hire_Date TEXT NOT NULL)''')
    
    cursor.execute('''CREATE TABLE Departments (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        Name TEXT NOT NULL UNIQUE,
                        Manager TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Insert sample data into both tables
def insert_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    employees = [
        ("Alice", "Sales", 50000, "2021-01-15"),
        ("Bob", "Engineering", 70000, "2020-06-10"),
        ("Charlie", "Marketing", 60000, "2022-03-20"),
    ]
    
    departments = [
        ("Sales", "Alice"),
        ("Engineering", "Bob"),
        ("Marketing", "Charlie"),
    ]

    cursor.executemany("INSERT INTO Employees (Name, Department, Salary, Hire_Date) VALUES (?, ?, ?, ?)", employees)
    cursor.executemany("INSERT INTO Departments (Name, Manager) VALUES (?, ?)", departments)
    conn.commit()
    conn.close()

# Function to execute queries
def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            result = cursor.fetchall()
            conn.close()
            return result
        else:
            conn.commit()
            conn.close()
            return None
    except sqlite3.Error as e:
        conn.close()
        return f"Database error: {e}"

# Function to handle user queries
def handle_user_query(query):
    query = query.lower().strip()

    # Query total salary expense in a department
    match = re.match(r'.*salary.*expense.*(?:in|of|for)?\s+(\w+)\s+department', query)
    if match:
        department = match.group(1).capitalize().strip()
        sql_query = "SELECT SUM(Salary) FROM Employees WHERE Department = ?"
        result = execute_query(sql_query, (department,), fetch=True)

        if result and result[0][0] is not None:
            return {"response": f"The total salary expense for the {department} department is ${result[0][0]:,.2f}."}
        else:
            return {"response": f"No salary data found for the {department} department."}

    # Query listing employees in a department
    match = re.match(r'.*employees.*(?:in|of|for)?\s+(\w+)\s+department', query)
    if match:
        department = match.group(1).capitalize().strip()
        sql_query = "SELECT Name FROM Employees WHERE Department = ?"
        result = execute_query(sql_query, (department,), fetch=True)

        if result:
            employees = ', '.join(row[0] for row in result)
            return {"response": f"Employees in the {department} department: {employees}."}
        else:
            return {"response": f"No employees found in the {department} department."}

    # Query for department managers
    match = re.match(r'.*manager.*(?:of|for)?\s+(\w+)\s+department', query)
    if match:
        department = match.group(1).capitalize().strip()
        sql_query = "SELECT Manager FROM Departments WHERE Name = ?"
        result = execute_query(sql_query, (department,), fetch=True)

        if result:
            return {"response": f"The manager of the {department} department is {result[0][0]}."}
        else:
            return {"response": f"No manager found for the {department} department."}

    return {"response": "Sorry, I didn't understand that query."}

@app.route('/query', methods=['GET'])
def query():
    user_query = request.args.get('q')
    if not user_query:
        return jsonify({"response": "Please provide a query parameter `q`."}), 400

    response = handle_user_query(user_query)
    return jsonify(response)

if __name__ == '__main__':
    create_tables()
    insert_sample_data()
    app.run(host='0.0.0.0', port=5000)
