from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_cors import CORS
from db_config import get_db_connection
import os
from flask import send_from_directory

# Serve the portfolio static site from the parent `portfolio` folder so
# the backend can serve the frontend (index.html, css, js, images) directly.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTFOLIO_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'portfolio'))

app = Flask(__name__, static_folder=PORTFOLIO_DIR, static_url_path='')
app.secret_key = 'your-secret-key-here'      # needed for flash messages

# Route root to the portfolio index.html
@app.route('/')
def site_index():
    return app.send_static_file('index.html')


# Serve admin static files (css/js) from portfolio-admin/static under /admin_static/
@app.route('/admin_static/<path:filename>')
def admin_static(filename):
    admin_static_dir = os.path.join(BASE_DIR, 'static')
    return send_from_directory(admin_static_dir, filename)

# Enable CORS for the frontend API routes
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})


# ----------------------------------------------------------------------
# Simple auth utilities
# ----------------------------------------------------------------------
def login_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapped


# ----------------------------------------------------------------------
# Admin Dashboard
# ----------------------------------------------------------------------
@app.route('/admin/dashboard')
@login_required
def dashboard():
    # Provide small dashboard metrics (e.g., total projects)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) AS cnt FROM projects")
        row = cursor.fetchone()
        projects_count = row['cnt'] if row else 0
    except Exception:
        # If DB is not available, fall back to zero and allow the page to render
        projects_count = 0
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass

    return render_template('admin_dashboard.html', projects_count=projects_count)


# ----------------------------------------------------------------------
# View Projects (admin)
# ----------------------------------------------------------------------
@app.route('/admin/projects')
@login_required
def admin_projects():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_projects.html', projects=projects)


# ----------------------------------------------------------------------
# Add New Project
# ----------------------------------------------------------------------
@app.route('/admin/projects/add', methods=['GET', 'POST'])
@login_required
def add_project():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        category = request.form.get('category', 'web')  # Default to 'web' if not specified

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute( 
            "INSERT INTO projects (name, description, category) VALUES (%s, %s, %s)",
            (name, description, category)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Project added successfully!', 'success')
        return redirect(url_for('admin_projects'))

    # For GET: also show existing projects on the add page so admin can see current list
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('add_project.html', projects=projects)


# ----------------------------------------------------------------------
# Edit Project (admin) – GET shows form, POST saves changes
# ----------------------------------------------------------------------
@app.route('/admin/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        category = request.form.get('category', 'web')

        cursor.execute(
            """UPDATE projects
               SET name = %s, description = %s, category = %s
               WHERE id = %s""",
            (name, description, category, project_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('admin_projects'))

    # GET – fetch current data
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    cursor.close()
    conn.close()

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('admin_projects'))

    return render_template('edit_project.html', project=project)


# ----------------------------------------------------------------------
# Delete Project (admin) – POST only
# ----------------------------------------------------------------------
@app.route('/admin/projects/delete/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('admin_projects'))


# ----------------------------------------------------------------------
# Authentication routes
# ----------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # Simple hardcoded auth — replace with DB lookup as needed
        if email == 'kravann.yorm@student.passerellesnumeriques.org' and password == '1234567':
            session['user'] = email
            return redirect(url_for('admin_projects'))
        else:
            error_message = 'Invalid email or password'
            return render_template('Login.html', error_message=error_message)

    # GET
    return render_template('Login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ----------------------------------------------------------------------
# API: List all projects
# ----------------------------------------------------------------------
@app.route('/api/projects', methods=['GET'])
def api_projects():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(projects)


# ----------------------------------------------------------------------
# API: Get a single project
# ----------------------------------------------------------------------
@app.route('/api/projects/<int:project_id>', methods=['GET'])
def api_get_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    cursor.close()
    conn.close()
    if project:
        return jsonify(project)
    return jsonify({'error': 'Project not found'}), 404


# ----------------------------------------------------------------------
# API: Create a project
# ----------------------------------------------------------------------
@app.route('/api/projects', methods=['POST'])
def api_create_project():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'name is required'}), 400
    name = data['name']
    description = data.get('description', '')
    category = data.get('category', 'web')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO projects (name, description, category) VALUES (%s, %s, %s)",
        (name, description, category)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return jsonify({'id': new_id, 'message': 'Project created'}), 201


# ----------------------------------------------------------------------
# API: Update a project (PUT)
# ----------------------------------------------------------------------
@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def api_update_project(project_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    name = data.get('name')
    description = data.get('description')
    category = data.get('category')

    if name is None and description is None and category is None:
        return jsonify({'error': 'At least one field (name/description/category) required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE projects
           SET name = COALESCE(%s, name),
               description = COALESCE(%s, description),
               category = COALESCE(%s, category)
           WHERE id = %s""",
        (name, description, category, project_id)
    )
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if affected == 0:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify({'message': 'Project updated'})


# ----------------------------------------------------------------------
# API: Delete a project
# ----------------------------------------------------------------------
@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if affected == 0:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify({'message': 'Project deleted successfully'})

from db_config import get_db_connection
try:
    conn = get_db_connection()
    print("Connected:", conn.is_connected())
    conn.close()
except Exception as e:
    print("DB error:", e)
# ----------------------------------------------------------------------
# Run the app
# ----------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)





