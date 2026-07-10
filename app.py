# ===============================================
# EMPLOYEE ONBOARDING FORM - COMPLETE BACKEND
# Python Flask Application
# ===============================================

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE = 'employee_onboarding.db'
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 25 * 1024 * 1024

# Create uploads folder
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# ===============================================
# DATABASE INITIALIZATION
# ===============================================

def init_database():
    """Initialize database with complete onboarding schema"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Main employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT UNIQUE,
            full_name TEXT,
            gender TEXT,
            dob DATE,
            blood_group TEXT,
            marital_status TEXT,
            personal_email TEXT,
            mobile_number TEXT,
            current_address TEXT,
            permanent_address TEXT,
            city TEXT,
            pin_code TEXT,
            date_of_joining DATE,
            department TEXT,
            designation TEXT,
            reporting_manager TEXT,
            company_name TEXT,
            work_location TEXT,
            aadhaar_number TEXT,
            aadhaar_file TEXT,
            pan_number TEXT,
            pan_file TEXT,
            account_holder_name TEXT,
            bank_name TEXT,
            account_number TEXT,
            ifsc_code TEXT,
            cancelled_cheque TEXT,
            highest_qualification TEXT,
            college_name TEXT,
            year_of_passing INTEGER,
            qualification_cert TEXT,
            passport_photo TEXT,
            is_fresher BOOLEAN,
            emergency_name TEXT,
            emergency_relationship TEXT,
            emergency_mobile TEXT,
            declaration1 BOOLEAN,
            declaration2 BOOLEAN,
            signature_name TEXT,
            signature_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Experience table (for experienced employees with multiple companies)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            company_name TEXT,
            designation TEXT,
            years_of_experience REAL,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')
    
    # Document references table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            document_type TEXT,
            file_name TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized with employee onboarding schema")

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

def allowed_file(filename):
    """Check if file is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, employee_code, doc_type):
    """Save file securely"""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        return None
    
    # Check file size
    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_FILE_SIZE:
        return None
    file.seek(0)
    
    # Generate secure filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = secure_filename(f"{employee_code}_{doc_type}_{timestamp}.{ext}")
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return filename

def generate_employee_code():
    """Generate unique employee code"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM employees')
    count = cursor.fetchone()[0]
    conn.close()
    
    timestamp = datetime.now().strftime('%Y%m%d')
    code = f"EMP{timestamp}{str(count + 1).zfill(3)}"
    return code

# ===============================================
# API ENDPOINTS
# ===============================================

@app.route('/')
def home():
    return render_template("employee_form_local.html")

@app.route('/submit-onboarding', methods=['POST'])
def submit_onboarding():
    """Submit complete onboarding form"""
    try:
        # Get form data
        data = request.form.to_dict()
        
        # Validate required fields
        required_fields = ['fullName', 'gender', 'dob', 'bloodGroup', 'maritalStatus',
                          'personalEmail', 'mobileNumber', 'currentAddress', 'permanentAddress',
                          'city', 'pinCode', 'dateOfJoining', 'department', 'designation',
                          'reportingManager', 'companyName', 'workLocation', 'aadhaarNumber',
                          'panNumber', 'accountHolderName', 'bankName', 'accountNumber',
                          'ifscCode', 'qualification', 'collegeName', 'yearOfPassing',
                          'fresher', 'emergencyName', 'emergencyRelationship', 'emergencyMobile',
                          'declaration1', 'declaration2', 'signatureName', 'signatureDate']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Validate files
        required_files = ['aadhaarFile', 'panFile', 'cancelledCheque', 
                         'qualificationCert', 'passportPhoto']
        
        for file_field in required_files:
            if file_field not in request.files or request.files[file_field].filename == '':
                return jsonify({
                    'status': 'error',
                    'message': f'{file_field} is required'
                }), 400
        
        # Generate employee code
        employee_code = generate_employee_code()
        
        # Save all files
        files_saved = {}
        for file_field in required_files:
            doc_type = file_field.replace('File', '').upper()
            filename = save_file(request.files[file_field], employee_code, doc_type)
            if not filename:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to save {file_field}'
                }), 400
            files_saved[file_field] = filename
        
        # Save optional experience documents (for experienced employees)
        optional_docs = {}
        if data.get('fresher') == 'No':
            for doc in ['experienceLetter', 'relievingLetter']:
                if doc in request.files and request.files[doc].filename != '':
                    filename = save_file(request.files[doc], employee_code, doc.upper())
                    if filename:
                        optional_docs[doc] = filename
        
        # Save to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO employees (
                employee_code, full_name, gender, dob, blood_group, marital_status,
                personal_email, mobile_number, current_address, permanent_address,
                city, pin_code, date_of_joining, department, designation,
                reporting_manager, company_name, work_location, aadhaar_number,
                aadhaar_file, pan_number, pan_file, account_holder_name, bank_name,
                account_number, ifsc_code, cancelled_cheque, highest_qualification,
                college_name, year_of_passing, qualification_cert, passport_photo,
                is_fresher, emergency_name, emergency_relationship, emergency_mobile,
                declaration1, declaration2, signature_name, signature_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            employee_code, data.get('fullName'), data.get('gender'), 
            data.get('dob'), data.get('bloodGroup'), data.get('maritalStatus'),
            data.get('personalEmail'), data.get('mobileNumber'), 
            data.get('currentAddress'), data.get('permanentAddress'),
            data.get('city'), data.get('pinCode'), data.get('dateOfJoining'),
            data.get('department'), data.get('designation'), data.get('reportingManager'),
            data.get('companyName'), data.get('workLocation'), data.get('aadhaarNumber'),
            files_saved['aadhaarFile'], data.get('panNumber'), files_saved['panFile'],
            data.get('accountHolderName'), data.get('bankName'), data.get('accountNumber'),
            data.get('ifscCode'), files_saved['cancelledCheque'], data.get('qualification'),
            data.get('collegeName'), data.get('yearOfPassing'), files_saved['qualificationCert'],
            files_saved['passportPhoto'], data.get('fresher') == 'Yes',
            data.get('emergencyName'), data.get('emergencyRelationship'), 
            data.get('emergencyMobile'), data.get('declaration1') == 'on',
            data.get('declaration2') == 'on', data.get('signatureName'),
            data.get('signatureDate')
        ))
        
        employee_id = cursor.lastrowid
        
        # Save experience if not fresher
        if data.get('fresher') == 'No':
            count = 1
            while f'expCompany{count}' in data:
                cursor.execute('''
                    INSERT INTO experience (employee_id, company_name, designation, years_of_experience)
                    VALUES (?, ?, ?, ?)
                ''', (
                    employee_id, data.get(f'expCompany{count}'),
                    data.get(f'expDesignation{count}'), data.get(f'expYears{count}')
                ))
                count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Welcome {data.get("fullName")}! Your onboarding is complete.',
            'employee_code': employee_code
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get-employees', methods=['GET'])
def get_employees():
    """Get all employees"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, employee_code, full_name, designation, company_name FROM employees')
        rows = cursor.fetchall()
        conn.close()
        
        employees = [{
            'id': row[0],
            'employee_code': row[1],
            'full_name': row[2],
            'designation': row[3],
            'company_name': row[4]
        } for row in rows]
        
        return jsonify({
            'status': 'success',
            'count': len(employees),
            'data': employees
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy'}), 200

# ===============================================
# ERROR HANDLERS
# ===============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Route not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# ===============================================
# MAIN EXECUTION
# ===============================================

# Initialize database when the application starts
init_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("\n" + "="*60)
    print("Employee Onboarding Backend Server")
    print("="*60)
    print(f"Server running on port: {port}")
    print(f"Database: {DATABASE}")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print("="*60 + "\n")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
