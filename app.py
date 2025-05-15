from flask import Flask, render_template, request, redirect, session, jsonify
import pymysql
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "16bcbf3d88e0347d08b15b437ecb72ba"  # Used for session management

# Database connection
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="23CSR207",
        database="student_performance",
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = "SELECT * FROM users WHERE username = %s AND password = %s"
                cursor.execute(query, (username, password))
                user = cursor.fetchone()
                if user:
                    session['username'] = username
                    session['role'] = user['role']
                    session['user_id'] = user['user_id']
                    if user['role'] == 'student':
                        return redirect('/dashboard')
                    elif user['role'] == 'teacher':
                        return redirect('/dash2')
                    elif user['role'] == 'admin':
                        return redirect('/admin')
                else:
                    return "Invalid username or password. <a href='/login'>Try Again</a>"
        finally:
            conn.close()
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if session.get('username') and session.get('role') == 'student':
        student_id = session.get('user_id')
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Fetch student details
                cursor.execute("SELECT name, roll_number FROM students WHERE student_id = %s", (student_id,))
                student = cursor.fetchone()
                if not student:
                    return "Student data not found. Contact admin.", 404

                # Fetch marks
                cursor.execute("""
                    SELECT s.subject_name, m.marks_obtained, m.total_marks, m.exam_date, m.exam_type 
                    FROM marks m
                    JOIN subjects s ON m.subject_id = s.subject_id
                    WHERE m.student_id = %s
                    ORDER BY m.exam_date DESC
                """, (student_id,))
                marks = cursor.fetchall()

                # Fetch latest attendance
                cursor.execute("""
                    SELECT date, status, subject_name 
                    FROM attendance a
                    JOIN subjects s ON a.subject_id = s.subject_id
                    WHERE a.student_id = %s
                    ORDER BY date DESC LIMIT 1
                """, (student_id,))
                attendance = cursor.fetchone()

                # Fetch total SAP points
                cursor.execute("""
                    SELECT SUM(points) as total_points 
                    FROM sap_requests 
                    WHERE student_id = %s AND status = 'Approved'
                """, (student_id,))
                total_sap_points = cursor.fetchone()['total_points'] or 0

            return render_template('dashboard.html', 
                                 student=student, 
                                 marks=marks, 
                                 attendance=attendance, 
                                 total_sap_points=total_sap_points)
        finally:
            conn.close()
    return redirect('/login')

@app.route('/submit_sap', methods=['POST'])
def submit_sap():
    if session.get('role') != 'student':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    student_id = session.get('user_id')
    data = request.form
    date = data.get('date')
    event_type = data.get('event_type')
    conducted_by = data.get('conducted_by')
    inside_outside = data.get('inside_outside')
    location = data.get('location')
    prize = data.get('prize')
    proof_link = data.get('proof_link')

    if not all([date, event_type, conducted_by, inside_outside, location]):
        return jsonify({'status': 'error', 'message': 'All required fields must be filled'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                INSERT INTO sap_requests 
                (student_id, date, event_type, conducted_by, inside_outside, location, prize, proof_link, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Pending')
            """
            cursor.execute(query, (student_id, date, event_type, conducted_by, inside_outside, location, prize, proof_link))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'SAP request submitted successfully'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'Error submitting SAP request: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/sap_history')
def sap_history():
    if session.get('username') and session.get('role') == 'student':
        student_id = session.get('user_id')
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT date, event_type, conducted_by, inside_outside, location, prize, 
                           proof_link, status, points, rejection_reason
                    FROM sap_requests 
                    WHERE student_id = %s 
                    ORDER BY date DESC
                """, (student_id,))
                sap_requests = cursor.fetchall()
                cursor.execute("SELECT name, roll_number FROM students WHERE student_id = %s", (student_id,))
                student = cursor.fetchone()
            return render_template('sap_history.html', sap_requests=sap_requests, student=student)
        finally:
            conn.close()
    return redirect('/login')

@app.route('/marks_report')
def marks_report():
    if session.get('username') and session.get('role') == 'student':
        student_id = session.get('user_id')
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT s.subject_name, m.marks_obtained, m.total_marks, m.exam_date, m.exam_type 
                    FROM marks m
                    JOIN subjects s ON m.subject_id = s.subject_id
                    WHERE m.student_id = %s
                    ORDER BY m.exam_date DESC
                """, (student_id,))
                marks = cursor.fetchall()
                cursor.execute("SELECT name, roll_number FROM students WHERE student_id = %s", (student_id,))
                student = cursor.fetchone()
            return render_template('marks_report.html', marks=marks, student=student)
        finally:
            conn.close()
    return redirect('/login')

@app.route('/sap_report')
def sap_report():
    if session.get('username') and session.get('role') == 'student':
        student_id = session.get('user_id')
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT date, event_type, conducted_by, inside_outside, location, prize, 
                           proof_link, status, points
                    FROM sap_requests 
                    WHERE student_id = %s AND status = 'Approved'
                    ORDER BY date DESC
                """, (student_id,))
                sap_requests = cursor.fetchall()
                cursor.execute("SELECT SUM(points) as total_points FROM sap_requests WHERE student_id = %s AND status = 'Approved'", (student_id,))
                total_points = cursor.fetchone()['total_points'] or 0
                cursor.execute("SELECT name, roll_number FROM students WHERE student_id = %s", (student_id,))
                student = cursor.fetchone()
            return render_template('sap_report.html', sap_requests=sap_requests, total_points=total_points, student=student)
        finally:
            conn.close()
    return redirect('/login')

@app.route('/dash2')
def dash2():
    if session.get('username') and session.get('role') == 'teacher':
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM students")
                students = cursor.fetchall()
            return render_template('dash2.html', students=students)
        except Exception as e:
            print("Error fetching students:", e)
            return "An error occurred while fetching data."
        finally:
            conn.close()
    return redirect('/login')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/admin')
def admin_dashboard():
    if session.get('username') and session.get('role') == 'admin':
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id, username, password, role FROM users")
                users = cursor.fetchall()
                cursor.execute("SELECT student_id, name, roll_number, class, section, gender FROM students")
                students = cursor.fetchall()
                cursor.execute("SELECT subject_id, subject_name FROM subjects")
                subjects = cursor.fetchall()
                cursor.execute("""
                    SELECT sr.id, sr.student_id, s.name, s.roll_number, sr.date, sr.event_type, 
                           sr.conducted_by, sr.inside_outside, sr.location, sr.prize, 
                           sr.proof_link, sr.status, sr.points, sr.rejection_reason
                    FROM sap_requests sr
                    JOIN students s ON sr.student_id = s.student_id
                    WHERE sr.status = 'Pending'
                """)
                sap_requests = cursor.fetchall()
                settings = {
                    'system_name': 'Student Performance System',
                    'default_password': 'default123'
                }
            return render_template('admin.html', 
                                 users=users, 
                                 students=students, 
                                 subjects=subjects,
                                 sap_requests=sap_requests,
                                 settings=settings)
        finally:
            conn.close()
    return redirect('/login')

@app.route('/admin/approve_sap/<int:id>', methods=['POST'])
def approve_sap(id):
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    data = request.get_json()
    points = data.get('points')
    if not points or int(points) <= 0:
        return jsonify({'status': 'error', 'message': 'Valid points are required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE sap_requests SET status = 'Approved', points = %s 
                WHERE id = %s AND status = 'Pending'
            """, (points, id))
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'SAP request not found or already processed'}), 404
            conn.commit()
            return jsonify({'status': 'success', 'message': 'SAP request approved successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'Error approving SAP request: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/admin/reject_sap/<int:id>', methods=['POST'])
def reject_sap(id):
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        rejection_reason = data.get('rejection_reason', '')
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # First check if the SAP request exists
            cursor.execute("SELECT * FROM sap_requests WHERE id = %s", (id,))
            sap_request = cursor.fetchone()
            
            if not sap_request:
                return jsonify({'status': 'error', 'message': 'SAP request not found'}), 404
            
            # Update the status and rejection reason
            cursor.execute("""
                UPDATE sap_requests 
                SET status = 'Rejected', 
                    rejection_reason = %s,
                    points = NULL
                WHERE id = %s
            """, (rejection_reason, id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return jsonify({'status': 'success', 'message': 'SAP request rejected successfully'}), 200
            else:
                conn.rollback()
                return jsonify({'status': 'error', 'message': 'Failed to reject SAP request'}), 500
                
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': f'Error rejecting SAP request: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/get_all_users', methods=['GET'])
def get_all_users():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id, username, role FROM users")
            users = cursor.fetchall()
            result = [{'user_id': user['user_id'], 'username': user['username'], 'role': user['role']} for user in users]
        return jsonify({'users': result})
    finally:
        conn.close()

@app.route('/admin/create_user', methods=['POST'])
def create_user():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    data = request.get_json()
    user_id = data.get('user_id')  # Get user_id from form data
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    if not user_id or not username or not password or not role:
        return jsonify({'status': 'error', 'message': 'User ID, username, password, and role are required'}), 400
    if role not in ['admin', 'teacher', 'student']:
        return jsonify({'status': 'error', 'message': 'Invalid role'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Username already exists'}), 400
            query = "INSERT INTO users (user_id, username, password, role) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user_id, username, password, role))
            conn.commit()
        return jsonify({'status': 'success', 'message': 'User created successfully'}), 201
    
    finally:
        conn.close()

@app.route('/admin/get_user_data', methods=['GET'])
def get_user_data():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    user_id = request.args.get('user_id')
    role = request.args.get('role')
    if not user_id or not role:
        return jsonify({'status': 'error', 'message': 'User ID and role are required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_id, username, password, role FROM users WHERE user_id = %s AND role = %s", (user_id, role))
            user = cursor.fetchone()
            if not user:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
        return jsonify({
            'user_id': user['user_id'],
            'username': user['username'],
            'password': user['password'],
            'role': user['role']
        })
    finally:
        conn.close()

@app.route('/admin/update_user', methods=['POST'])
def update_user():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    data = request.get_json()
    user_id = data.get('user_id')
    role = data.get('role')
    username = data.get('username')
    password = data.get('password')
    new_role = data.get('new_role')
    if not user_id or not role or not username or not new_role:
        return jsonify({'status': 'error', 'message': 'User ID, role, username, and new role are required'}), 400
    if new_role not in ['admin', 'teacher', 'student']:
        return jsonify({'status': 'error', 'message': 'Invalid role'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s AND (user_id != %s OR role != %s)", (username, user_id, role))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Username already exists'}), 400
            query = "UPDATE users SET username = %s, password = %s, role = %s WHERE user_id = %s AND role = %s"
            cursor.execute(query, (username, password or '', new_role, user_id, role))
            conn.commit()
        return jsonify({'status': 'success', 'message': 'User updated successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'Error updating user: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/admin/delete_user', methods=['DELETE'])
def delete_user():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    user_id = request.args.get('user_id')
    role = request.args.get('role')
    if not user_id or not role:
        return jsonify({'status': 'error', 'message': 'User ID and role are required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE user_id = %s AND role = %s", (user_id, role))
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'User not found'}), 404
            conn.commit()
        return jsonify({'status': 'success', 'message': 'User deleted successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'Error deleting user: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/admin/create_student', methods=['POST'])
def create_student():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    try:
        data = request.form.to_dict() if request.form else request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        name = data.get('name', '').strip()
        roll_number = data.get('roll_number', '').strip()
        class_name = data.get('class', '').strip()
        section = data.get('section', '').strip()
        gender = data.get('gender', '').strip()
        
        # Validate required fields
        if not name or not roll_number:
            return jsonify({'status': 'error', 'message': 'Name and Roll Number are required'}), 400
            
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if roll number already exists
                cursor.execute("SELECT student_id FROM students WHERE roll_number = %s", (roll_number,))
                if cursor.fetchone():
                    return jsonify({'status': 'error', 'message': 'Roll number already exists'}), 400
                    
                # Insert new student
                query = "INSERT INTO students (name, roll_number, class, section, gender) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query, (name, roll_number, class_name, section, gender))
                student_id = cursor.lastrowid
                conn.commit()
                
                # Fetch the created student for confirmation
                cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
                new_student = cursor.fetchone()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Student created successfully',
                    'student': {
                        'id': new_student['student_id'],
                        'name': new_student['name'],
                        'roll_number': new_student['roll_number'],
                        'class': new_student['class'],
                        'section': new_student['section'],
                        'gender': new_student['gender']
                    }
                }), 201
                
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/get_student_data', methods=['GET'])
def get_student_data():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    student_id = request.args.get('id')
    if not student_id:
        return jsonify({'status': 'error', 'message': 'Student ID is required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            if not student:
                return jsonify({'status': 'error', 'message': 'Student not found'}), 404
        return jsonify({
            'id': student['student_id'],
            'name': student['name'],
            'roll_number': student['roll_number'],
            'class': student['class'],
            'section': student['section'],
            'gender': student['gender']
        })
    finally:
        conn.close()

@app.route('/admin/delete_student/<int:id>', methods=['DELETE'])
def delete_student(id):
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Start transaction
            cursor.execute("START TRANSACTION")
            
            # Delete related records first
            cursor.execute("DELETE FROM attendance WHERE student_id = %s", (id,))
            cursor.execute("DELETE FROM marks WHERE student_id = %s", (id,))
            cursor.execute("DELETE FROM student_subjects WHERE student_id = %s", (id,))
            cursor.execute("DELETE FROM sap_requests WHERE student_id = %s", (id,))
            
            # Finally delete the student
            cursor.execute("DELETE FROM students WHERE student_id = %s", (id,))
            if cursor.rowcount == 0:
                conn.rollback()
                return jsonify({'status': 'error', 'message': 'Student not found'}), 404
                
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Student deleted successfully'}), 200
            
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/get_student_subjects', methods=['GET'])
def get_student_subjects():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    student_id = request.args.get('student_id')
    if not student_id:
        return jsonify({'status': 'error', 'message': 'Student ID is required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT ss.subject_id, s.subject_name 
                FROM student_subjects ss
                JOIN subjects s ON ss.subject_id = s.subject_id
                WHERE ss.student_id = %s
            """, (student_id,))
            subjects = cursor.fetchall()
            result = [{'subject_id': subject['subject_id'], 'subject_name': subject['subject_name']} for subject in subjects]
        return jsonify({'subjects': result})
    finally:
        conn.close()

@app.route('/admin/assign_subjects', methods=['POST'])
def assign_subjects():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    try:
        data = request.form.to_dict() if request.form else request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        student_id = data.get('student_id')
        subject_ids = data.get('subject_ids')
        
        if not student_id or not subject_ids:
            return jsonify({'status': 'error', 'message': 'Student ID and subject IDs are required'}), 400
            
        try:
            student_id = int(student_id)
            if isinstance(subject_ids, str):
                if subject_ids.startswith('['):
                    import json
                    subject_ids = json.loads(subject_ids)
                else:
                    subject_ids = [int(x.strip()) for x in subject_ids.split(',') if x.strip()]
            elif isinstance(subject_ids, list):
                subject_ids = [int(x) for x in subject_ids]
        except (ValueError, json.JSONDecodeError):
            return jsonify({'status': 'error', 'message': 'Invalid student ID or subject IDs format'}), 400
            
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Verify student exists
                cursor.execute("SELECT name FROM students WHERE student_id = %s", (student_id,))
                student = cursor.fetchone()
                if not student:
                    return jsonify({'status': 'error', 'message': 'Student not found'}), 404
                    
                # Verify subjects exist
                subject_list = ','.join(['%s'] * len(subject_ids))
                cursor.execute(f"SELECT subject_id, subject_name FROM subjects WHERE subject_id IN ({subject_list})", tuple(subject_ids))
                subjects = cursor.fetchall()
                if len(subjects) != len(subject_ids):
                    return jsonify({'status': 'error', 'message': 'One or more subjects not found'}), 404
                    
                # Start transaction
                cursor.execute("START TRANSACTION")
                
                # Remove existing assignments
                cursor.execute("DELETE FROM student_subjects WHERE student_id = %s", (student_id,))
                
                # Add new assignments
                for subject_id in subject_ids:
                    cursor.execute("""
                        INSERT INTO student_subjects (student_id, subject_id) 
                        VALUES (%s, %s)
                    """, (student_id, subject_id))
                    
                conn.commit()
                return jsonify({
                    'status': 'success',
                    'message': 'Subjects assigned successfully',
                    'student_name': student['name'],
                    'subjects': [{'id': s['subject_id'], 'name': s['subject_name']} for s in subjects]
                }), 200
                
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/remove_subject', methods=['POST'])
def remove_subject():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    data = request.get_json()
    student_id = data.get('student_id')
    subject_id = data.get('subject_id')
    if not student_id or not subject_id:
        return jsonify({'status': 'error', 'message': 'Student ID and subject ID are required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM student_subjects WHERE student_id = %s AND subject_id = %s", 
                          (student_id, subject_id))
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'Subject not assigned to student'}), 404
            conn.commit()
        return jsonify({'status': 'success', 'message': 'Subject removed successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'Error removing subject: {str(e)}'}), 500
    finally: 
        conn.close()

@app.route('/admin/update_student/<int:id>', methods=['POST'])
def update_student(id):
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    data = request.get_json()
    name = data.get('name')
    roll_number = data.get('roll_number')
    class_name = data.get('class')
    section = data.get('section')
    gender = data.get('gender')
    if not name or not roll_number:
        return jsonify({'status': 'error', 'message': 'Name and Roll Number are required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM students WHERE roll_number = %s AND student_id != %s", (roll_number, id))
            if cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Roll number already exists'}), 400
            query = "UPDATE students SET name = %s, roll_number = %s, class = %s, section = %s, gender = %s WHERE student_id = %s"
            cursor.execute(query, (name, roll_number, class_name, section, gender, id))
            conn.commit()
        return jsonify({'status': 'success', 'message': 'Student updated successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'Error updating student: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/admin/get_subject_data', methods=['GET'])
def get_subject_data():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    subject_id = request.args.get('id')
    if not subject_id:
        return jsonify({'status': 'error', 'message': 'Subject ID is required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM subjects WHERE subject_id = %s", (subject_id,))
            subject = cursor.fetchone()
            if not subject:
                return jsonify({'status': 'error', 'message': 'Subject not found'}), 404
        return jsonify({
            'id': subject['subject_id'],
            'subject_name': subject['subject_name']
        })
    finally:
        conn.close()

@app.route('/admin/update_subject/<int:id>', methods=['POST'])
def update_subject(id):
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    data = request.get_json()
    subject_name = data.get('subject_name')
    if not subject_name:
        return jsonify({'status': 'error', 'message': 'Subject name is required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = "UPDATE subjects SET subject_name = %s WHERE subject_id = %s"
            cursor.execute(query, (subject_name, id))
            conn.commit()
        return jsonify({'status': 'success', 'message': 'Subject updated successfully'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': f'Error updating subject: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/admin/delete_subject/<int:id>', methods=['DELETE'])
def delete_subject(id):
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Start transaction
            cursor.execute("START TRANSACTION")
            
            # Check for dependencies
            cursor.execute("SELECT COUNT(*) as count FROM student_subjects WHERE subject_id = %s", (id,))
            if cursor.fetchone()['count'] > 0:
                return jsonify({'status': 'error', 'message': 'Cannot delete subject that is assigned to students'}), 400
                
            cursor.execute("SELECT COUNT(*) as count FROM attendance WHERE subject_id = %s", (id,))
            if cursor.fetchone()['count'] > 0:
                return jsonify({'status': 'error', 'message': 'Cannot delete subject that has attendance records'}), 400
                
            cursor.execute("SELECT COUNT(*) as count FROM marks WHERE subject_id = %s", (id,))
            if cursor.fetchone()['count'] > 0:
                return jsonify({'status': 'error', 'message': 'Cannot delete subject that has marks records'}), 400
                
            # Delete the subject if no dependencies
            cursor.execute("DELETE FROM subjects WHERE subject_id = %s", (id,))
            if cursor.rowcount == 0:
                conn.rollback()
                return jsonify({'status': 'error', 'message': 'Subject not found'}), 404
                
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Subject deleted successfully'}), 200
            
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/create_subject', methods=['POST'])
def create_subject():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    try:
        data = request.form.to_dict() if request.form else request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        subject_name = data.get('subject_name', '').strip()
        
        if not subject_name:
            return jsonify({'status': 'error', 'message': 'Subject name is required'}), 400
            
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Check if subject already exists
                cursor.execute("SELECT subject_id FROM subjects WHERE subject_name = %s", (subject_name,))
                if cursor.fetchone():
                    return jsonify({'status': 'error', 'message': 'Subject already exists'}), 400
                    
                # Insert new subject
                cursor.execute("INSERT INTO subjects (subject_name) VALUES (%s)", (subject_name,))
                subject_id = cursor.lastrowid
                conn.commit()
                
                # Fetch the created subject for confirmation
                cursor.execute("SELECT * FROM subjects WHERE subject_id = %s", (subject_id,))
                new_subject = cursor.fetchone()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Subject created successfully',
                    'subject': {
                        'id': new_subject['subject_id'],
                        'name': new_subject['subject_name']
                    }
                }), 201
                
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/get_students_for_attendance', methods=['GET'])
def get_students_for_attendance():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    date = request.args.get('date')
    if not date:
        return jsonify({'status': 'error', 'message': 'Date is required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM students")
            students = cursor.fetchall()
            result = []
            for student in students:
                cursor.execute("SELECT status FROM attendance WHERE student_id = %s AND date = %s", (student['student_id'], date))
                status = cursor.fetchone()
                result.append({
                    'id': student['student_id'],
                    'name': student['name'],
                    'roll_number': student['roll_number'],
                    'status': status['status'] if status else 'Present'
                })
        return jsonify({'students': result})
    finally:
        conn.close()

@app.route('/admin/update_attendance', methods=['POST'])
def update_attendance():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()  # Convert form data to dict
            
        student_id = data.get('student_id')
        date = data.get('date')
        status = data.get('status')
        subject_id = data.get('subject_id')
        
        if not all([student_id, date, status, subject_id]):
            return jsonify({'status': 'error', 'message': 'All fields are required'}), 400
            
        # Convert student_id and subject_id to integers
        try:
            student_id = int(student_id)
            subject_id = int(subject_id)
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Invalid student ID or subject ID'}), 400
            
        if status not in ['Present', 'Absent']:
            return jsonify({'status': 'error', 'message': 'Status must be either Present or Absent'}), 400
            
        # Validate date format
        try:
            if isinstance(date, str):
                datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Verify student exists
                cursor.execute("SELECT 1 FROM students WHERE student_id = %s", (student_id,))
                if not cursor.fetchone():
                    return jsonify({'status': 'error', 'message': 'Student not found'}), 404
                    
                # Verify subject exists
                cursor.execute("SELECT 1 FROM subjects WHERE subject_id = %s", (subject_id,))
                if not cursor.fetchone():
                    return jsonify({'status': 'error', 'message': 'Subject not found'}), 404
                    
                # Verify student is assigned to the subject
                cursor.execute("""
                    SELECT 1 FROM student_subjects 
                    WHERE student_id = %s AND subject_id = %s
                """, (student_id, subject_id))
                
                if not cursor.fetchone():
                    return jsonify({'status': 'error', 'message': 'Student is not assigned to this subject'}), 400
                    
                # Update or insert attendance record
                cursor.execute("""
                    INSERT INTO attendance (student_id, date, status, subject_id)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE status = VALUES(status)
                """, (student_id, date, status, subject_id))
                
                conn.commit()
                return jsonify({
                    'status': 'success',
                    'message': 'Attendance updated successfully',
                    'details': {
                        'student_id': student_id,
                        'date': date,
                        'status': status,
                        'subject_id': subject_id
                    }
                }), 200
                
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error updating attendance: {str(e)}'}), 500
        
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/admin/create_mark', methods=['POST'])
def create_mark():
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    try:
        data = request.form.to_dict() if request.form else request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        student_id = data.get('student_id')
        subject_id = data.get('subject_id')
        marks_obtained = data.get('marks_obtained')
        total_marks = data.get('total_marks')
        exam_date = data.get('exam_date')
        exam_type = data.get('exam_type')
        
        if not all([student_id, subject_id, marks_obtained, total_marks, exam_date, exam_type]):
            return jsonify({'status': 'error', 'message': 'All fields are required'}), 400
            
        try:
            student_id = int(student_id)
            subject_id = int(subject_id)
            marks_obtained = float(marks_obtained)
            total_marks = float(total_marks)
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid numeric values'}), 400
            
        if marks_obtained > total_marks:
            return jsonify({'status': 'error', 'message': 'Marks obtained cannot be greater than total marks'}), 400
            
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Verify student exists
                cursor.execute("SELECT name FROM students WHERE student_id = %s", (student_id,))
                student = cursor.fetchone()
                if not student:
                    return jsonify({'status': 'error', 'message': 'Student not found'}), 404
                    
                # Verify subject exists
                cursor.execute("SELECT subject_name FROM subjects WHERE subject_id = %s", (subject_id,))
                subject = cursor.fetchone()
                if not subject:
                    return jsonify({'status': 'error', 'message': 'Subject not found'}), 404
                    
                # Verify student is assigned to subject
                cursor.execute("""
                    SELECT 1 FROM student_subjects 
                    WHERE student_id = %s AND subject_id = %s
                """, (student_id, subject_id))
                if not cursor.fetchone():
                    return jsonify({'status': 'error', 'message': 'Student is not assigned to this subject'}), 400
                    
                # Check if mark already exists
                cursor.execute("""
                    SELECT 1 FROM marks 
                    WHERE student_id = %s AND subject_id = %s AND exam_type = %s AND exam_date = %s
                """, (student_id, subject_id, exam_type, exam_date))
                if cursor.fetchone():
                    return jsonify({'status': 'error', 'message': 'Mark already exists for this exam'}), 400
                    
                # Insert mark
                cursor.execute("""
                    INSERT INTO marks (student_id, subject_id, marks_obtained, total_marks, exam_date, exam_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (student_id, subject_id, marks_obtained, total_marks, exam_date, exam_type))
                
                conn.commit()
                return jsonify({
                    'status': 'success',
                    'message': 'Marks entered successfully',
                    'details': {
                        'student_name': student['name'],
                        'subject_name': subject['subject_name'],
                        'marks_obtained': marks_obtained,
                        'total_marks': total_marks,
                        'exam_type': exam_type,
                        'exam_date': exam_date
                    }
                }), 201
                
        except Exception as e:
            conn.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500
        finally:
            conn.close()
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin/get_marks/<int:student_id>', methods=['GET'])
def get_marks(student_id):
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT m.mark_id, m.student_id, s.subject_name, m.marks_obtained, 
                       m.total_marks, m.exam_date, m.exam_type
                FROM marks m
                JOIN subjects s ON m.subject_id = s.subject_id
                WHERE m.student_id = %s
            """, (student_id,))
            marks = cursor.fetchall()
            result = [{
                'id': mark['mark_id'],
                'student_id': mark['student_id'],
                'subject_name': mark['subject_name'],
                'marks_obtained': mark['marks_obtained'],
                'total_marks': mark['total_marks'],
                'exam_date': mark['exam_date'].strftime('%Y-%m-%d') if mark['exam_date'] else '',
                'exam_type': mark['exam_type']
            } for mark in marks]
        return jsonify({'marks': result})
    finally:
        conn.close()

@app.route('/admin/delete_mark/<int:id>', methods=['DELETE'])
def delete_mark(id):
    if session.get('role') != 'admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM marks WHERE mark_id = %s", (id,))
            if cursor.rowcount == 0:
                return jsonify({'status': 'error', 'message': 'Mark not found'}), 404
                
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Mark deleted successfully'}), 200
            
    except Exception as e:
        conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/')
def home():
    return redirect('/login')
@app.route('/student_subjects/<int:student_id>')  # specify int if student_id is numeric
def student_subjects(student_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Fetch student details
            cursor.execute(
                "SELECT student_id, name FROM students WHERE student_id = %s", 
                (student_id,)
            )
            student = cursor.fetchone()

            if not student:
                return "Student not found", 404

            # Fetch subjects for the student
            cursor.execute("""
                SELECT ss.subject_id, s.subject_name 
                FROM student_subjects ss
                JOIN subjects s ON ss.subject_id = s.subject_id
                WHERE ss.student_id = %s
            """, (student_id,))
            subjects = cursor.fetchall()

            return render_template('student_subjects.html', student=student, subjects=subjects)

    finally:
        conn.close()
    
@app.route('/marks/<student_id>')
def marks(student_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.subject_name, m.marks_obtained, m.exam_date, m.exam_type 
                FROM marks m
                JOIN subjects s ON m.subject_id = s.subject_id
                WHERE m.student_id = %s
            """, (student_id,))
            marks = cursor.fetchall()
        return render_template('marks.html', marks=marks, student_id=student_id)
    finally:
        conn.close()

@app.route('/attendance/<student_id>')
def attendance(student_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.date, a.status, s.subject_name 
                FROM attendance a
                JOIN subjects s ON a.subject_id = s.subject_id
                WHERE a.student_id = %s
                ORDER BY a.date ASC
            """, (student_id,))
            attendance_records = cursor.fetchall()
            if not attendance_records:
                return render_template('attendance.html', attendance=[], student_id=student_id)
        return render_template('attendance.html', attendance=attendance_records, student_id=student_id)
    finally:
        conn.close()
@app.route('/attendance/<student_id>/<int:subject_id>')
def student_attendance(student_id, subject_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # First get the student details
            cursor.execute("SELECT name, roll_number FROM students WHERE student_id = %s", (student_id,))
            student_result = cursor.fetchone()
            student_name = student_result['name'] if student_result else "Unknown Student"
            student_roll = student_result['roll_number'] if student_result else "Unknown"
            
            # Get the subject name for display
            cursor.execute("SELECT subject_name FROM subjects WHERE subject_id = %s", (subject_id,))
            subject_result = cursor.fetchone()
            subject_name = subject_result['subject_name'] if subject_result else "Unknown Subject"
            
            # Then get the attendance records
            cursor.execute("""
                SELECT a.date, a.status, s.subject_name
                FROM attendance a
                LEFT JOIN subjects s ON a.subject_id = s.subject_id
                WHERE a.student_id = %s AND a.subject_id = %s
                ORDER BY a.date ASC
            """, (student_id, subject_id))
            attendance_records = cursor.fetchall()
            
        return render_template('attendance_subject.html', 
                             attendance=attendance_records, 
                             student_id=student_id,
                             student_name=student_name,
                             student_roll=student_roll,
                             subject_id=subject_id,
                             subject_name=subject_name)
    finally:
        conn.close()
                        
@app.route('/performance/<student_id>/<int:subject_id>')
def performance_subject(student_id, subject_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT name, roll_number FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            if not student:
                return f"Error: No student found with ID {student_id}"
            cursor.execute("SELECT subject_name FROM subjects WHERE subject_id = %s", (subject_id,))
            subject = cursor.fetchone()
            if not subject:
                return f"Error: No subject found with ID {subject_id}"
            cursor.execute("""
                SELECT exam_type, marks_obtained, total_marks 
                FROM marks 
                WHERE student_id = %s AND subject_id = %s
            """, (student_id, subject_id))
            marks_data = cursor.fetchall()
            if not marks_data:
                return f"No marks data available for Student {student['name']} in {subject['subject_name']}."
            exam_types = [row['exam_type'] for row in marks_data]
            marks_obtained = [row['marks_obtained'] for row in marks_data]
            total_marks = [row['total_marks'] for row in marks_data]
        if not os.path.exists("static"):
            os.makedirs("static")
        bar_graph_path = f"static/{student_id}_{subject_id}_bar.png"
        line_graph_path = f"static/{student_id}_{subject_id}_line.png"
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8, 5))
        plt.bar(exam_types, total_marks, color='green', alpha=0.5, label="Total Marks")
        plt.bar(exam_types, marks_obtained, color='blue', label="Marks Obtained")
        plt.xlabel("Exam Type")
        plt.ylabel("Marks")
        plt.title(f"Marks Distribution for {subject['subject_name']}")
        plt.legend()
        plt.savefig(bar_graph_path)
        plt.close()
        plt.figure(figsize=(8, 5))
        plt.plot(exam_types, marks_obtained, marker='o', linestyle='-', color='blue', label="Marks Obtained")
        plt.plot(exam_types, total_marks, marker='s', linestyle='--', color='red', label="Total Marks")
        plt.xlabel("Exam Type")
        plt.ylabel("Marks")
        plt.title(f"Marks Trend for {subject['subject_name']}")
        plt.legend()
        plt.savefig(line_graph_path)
        plt.close()
        return render_template('performance_subject.html',
                             student=student,
                             subject=subject,
                             exam_types=exam_types,
                             marks_obtained=marks_obtained,
                             total_marks=total_marks,
                             bar_graph=bar_graph_path,
                             line_graph=line_graph_path)
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)