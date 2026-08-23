from init_db import create_tables
import os
import sqlite3
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
create_tables()
# Security: Secret key for session management and anti-tampering
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_bus_pass_key_2026')

# Define upload directory for user photos
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# SERVER-SIDE PRICE LOCKING: Prevents incorrect pricing and price tampering
PASS_PRICES = {
    'daily': 5.00,
    'monthly': 50.00,
    'quarterly': 135.00,
    'yearly': 500.00
}

def get_db_connection():
    """Establishes thread-safe database connection."""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# --- HEALTH CHECK FOR CLOUD LOAD BALANCERS & AUTO SCALING ---
@app.route('/health')
def health_check():
    """Used by AWS Target Groups / Cloud Run to monitor instance reliability."""
    try:
        conn = get_db_connection()
        conn.execute('SELECT 1')
        conn.close()
        return jsonify(status="healthy", database="connected"), 200
    except Exception as e:
        return jsonify(status="unhealthy", error=str(e)), 500


# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles user registration with password hashing to prevent theft."""
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        raw_password = request.form.get('password')

        if not email or not raw_password or not username:
            flash('All required fields must be filled out.', 'danger')
            return redirect(url_for('register'))

        # PREVENT THEFT: Secure password hashing
        hashed_password = generate_password_hash(raw_password, method='pbkdf2:sha256')

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (full_name, username, email, phone, password) VALUES (?, ?, ?, ?, ?)',
                (full_name, username, email, phone, hashed_password)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('An account with this Email or Username already exists.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles secure authentication using password hash checks."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        # PREVENT THEFT: Verify stored hash against provided credentials
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    """Displays user active passes and booking history."""
    if 'user_id' not in session:
        flash('Please log in to access your dashboard.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    user_passes = conn.execute(
        'SELECT * FROM passes WHERE user_id = ? ORDER BY id DESC', 
        (user_id,)
    ).fetchall()
    conn.close()

    return render_template('dashboard.html', passes=user_passes)


@app.route('/apply', methods=['GET', 'POST'])
def apply_pass():
    """Issues passes with server-side price verification and unique pass tracking."""
    if 'user_id' not in session:
        flash('Please log in to apply for a pass.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        pass_type = request.form.get('pass_type')

        # PREVENT INCORRECT PRICING: Server-side validation against fixed pricing dict
        if pass_type not in PASS_PRICES:
            flash('Invalid pass type selected.', 'danger')
            return redirect(url_for('apply_pass'))

        calculated_price = PASS_PRICES[pass_type]
        user_id = session['user_id']

        # PREVENT TICKET LOSS & FORGERY: Unique, immutable UUID generation
        pass_uuid = f"BUS-{uuid.uuid4().hex[:8].upper()}"

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO passes (pass_uuid, user_id, pass_type, price, status) VALUES (?, ?, ?, ?, ?)',
            (pass_uuid, user_id, pass_type, calculated_price, 'Active')
        )
        conn.commit()
        conn.close()

        flash(f'Bus pass issued successfully! Pass ID: {pass_uuid}', 'success')
        return redirect(url_for('dashboard'))

    return render_template('apply.html')


@app.route('/admin')
def admin():
    """Admin dashboard to view all issued system passes."""
    if 'user_id' not in session:
        flash('Access restricted.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    all_passes = conn.execute(
        'SELECT passes.*, users.full_name, users.email FROM passes JOIN users ON passes.user_id = users.id ORDER BY passes.id DESC'
    ).fetchall()
    conn.close()

    return render_template('admin.html', passes=all_passes)


if __name__ == '__main__':
    # Production deployment will run via Gunicorn instead of debug server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)