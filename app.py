import os
from functools import wraps
from flask import Flask, render_template, request, send_from_directory, url_for, redirect, session, flash
from werkzeug.utils import secure_filename
from database1 import DatabaseManager, UserManager, CourseManager

# --- APP INITIALIZATION ---
app = Flask(__name__)
app.secret_key = 'a_very_secret_key_for_flash_messaging'  # Required for session and flash messages
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DATABASE & MANAGER INITIALIZATION ---
db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
course_manager = CourseManager(db_manager)

# --- ADMIN CREDENTIALS ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin" # Use a more secure password in a real application


# --- HELPER FUNCTIONS & DECORATORS ---

@app.template_filter('basename')
def basename_filter(path):
    """Jinja filter to get the basename of a file path."""
    if path:
        return os.path.basename(path)
    return ''

def save_image(file):
    """Saves an uploaded file securely and returns its path."""
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return file_path
    return None

def login_required(f):
    """Decorator to ensure a user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("You need to be logged in to view this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to ensure a user is an admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash("You need admin privileges to view this page.", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


# --- AUTHENTICATION & CORE ROUTES ---

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        search_input = request.form.get("searchcourse")
        course = course_manager.get_course(search_input)
        if course:
            return redirect(url_for("course_info", coursename=search_input))
        else:
            flash(f"Course '{search_input}' not found.", "warning")
    
    courses = course_manager.get_all_courses()
    return render_template("home.html", courses=courses)

@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        success, message = user_manager.create_user(
            username=request.form.get("username"),
            email=request.form.get("email"),
            password=request.form.get("password"),
            confirm_password=request.form.get("confirm_password"),
            image_path=save_image(request.files.get("image")),
            security_question=request.form.get("security_question"),
            security_answer=request.form.get("security_answer")
        )
        if success:
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash(message, "danger")
            return render_template("signup.html", error=message) # Pass error for immediate display
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['username'] = username
            session['is_admin'] = True
            flash("Admin login successful!", "success")
            return redirect(url_for('admin'))

        if user_manager.check_credentials(username, password):
            session['username'] = username
            session['is_admin'] = False
            session['cart'] = [] # Initialize empty cart on login
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", "danger")
            return render_template("login.html", error="Invalid username or password.")
            
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('home'))

@app.route('/login/forget', methods=["GET", "POST"])
def forget_password():
    if request.method == 'POST':
        username = request.form.get('username')
        security_answer = request.form.get('security_answer')
        # Here you would add logic to reset the password, maybe redirecting to a new page
        # For now, let's just check the answer
        user = user_manager.get_user(username)
        if user and user['security_answer'] == security_answer:
            flash("Security answer correct. Please implement password reset form.", "success")
            # In a real app, you would redirect to a page to set a new password
            return redirect(url_for('login'))
        else:
            flash("Username or security answer is incorrect.", "danger")

    return render_template("forget_password.html")

@app.route("/course/<coursename>", methods=["GET", "POST"])
def course_info(coursename):
    course = course_manager.get_course(coursename)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for('home'))
        
    if request.method == "POST":
        if 'username' not in session:
            flash("Please log in to add items to your cart.", "warning")
            return redirect(url_for('login'))
        
        cart = session.get('cart', [])
        if course['title'] not in cart:
            cart.append(course['title'])
            session['cart'] = cart
            flash(f"'{course['title']}' added to your cart.", "success")
        else:
            flash(f"'{course['title']}' is already in your cart.", "info")
        return redirect(url_for('course_info', coursename=coursename))

    return render_template("course.html", course=course)


# --- USER PANEL ROUTES ---

@app.route("/user/<username>", methods=["GET", "POST"])
@login_required
def user(username):
    if username != session.get('username'):
        flash("You can only view your own profile.", "danger")
        return redirect(url_for('home'))

    cart = session.get('cart', [])
    if request.method == "POST": # Handle removing from cart
        course_to_remove = request.form.get('name')
        if course_to_remove in cart:
            cart.remove(course_to_remove)
            session['cart'] = cart
            flash(f"'{course_to_remove}' removed from cart.", "info")

    user_data = user_manager.get_user(username)
    enrolled_titles = user_manager.get_user_courses(username)
    user_courses = [course_manager.get_course(c['course_title']) for c in enrolled_titles if course_manager.get_course(c['course_title'])]
    cart_courses = [course_manager.get_course(title) for title in cart if course_manager.get_course(title)]
    
    return render_template("userPanel.html", user=user_data, user_courses=user_courses, cart=cart_courses)

@app.route("/user/<username>/edit", methods=["GET", "POST"])
@login_required
def user_edit(username):
    if username != session.get('username'):
        return redirect(url_for('home'))
        
    if request.method == "POST":
        try:
            user_manager.update_user(
                username,
                email=request.form.get("email"),
                password=request.form.get("password"),
                image_path=save_image(request.files.get("image"))
            )
            flash("Profile updated successfully!", "success")
        except ValueError as e:
            flash(str(e), "danger")
        return redirect(url_for('user', username=username))
        
    user_data = user_manager.get_user(username)
    return render_template("userPanel_edit.html", user=user_data)

@app.route("/user/<username>/save")
@login_required
def user_save(username):
    if username != session.get('username'):
        return redirect(url_for('home'))
        
    cart = session.get('cart', [])
    if not cart:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('user', username=username))
        
    for course_title in cart:
        user_manager.add_course_to_user(username, course_title)
        
    session['cart'] = [] # Clear the cart
    flash("You have successfully enrolled in the new courses!", "success")
    return redirect(url_for('user', username=username))


# --- ADMIN ROUTES ---

@app.route("/admin")
@admin_required
def admin():
    return render_template("adminPanel.html")

@app.route("/admin/courses", methods=["POST", "GET"])
@admin_required
def admin_courses():
    if request.method == "POST":
        course_to_delete = request.form.get("delete")
        course_manager.delete_course(course_to_delete)
        flash(f"Course '{course_to_delete}' deleted.", "success")
        return redirect(url_for('admin_courses'))
        
    courses = course_manager.get_all_courses()
    return render_template("admin_courses.html", courses=courses)

@app.route("/admin/courses/add", methods=["GET", "POST"])
@admin_required
def admin_courses_add():
    if request.method == "POST":
        course_manager.create_course(
            title=request.form.get("title").lower(),
            description=request.form.get("description"),
            photo_path=save_image(request.files.get("image")),
            watch_hours=request.form.get("watch_hours"),
            class_day=request.form.get("class_day")
        )
        flash("Course added successfully.", "success")
        return redirect(url_for("admin_courses"))
    return render_template("admin_courses_add.html")

@app.route("/admin/courses/edit/<courseName>", methods=["GET", "POST"])
@admin_required
def admin_courses_edit(courseName):
    if request.method == "POST":
        course_manager.update_course(
            title=courseName,
            description=request.form.get("description"),
            photo_path=save_image(request.files.get("image")),
            watch_hours=request.form.get("watch_hours"),
            class_day=request.form.get("class_day")
        )
        flash("Course updated successfully.", "success")
        return redirect(url_for("admin_courses"))
        
    course_info = course_manager.get_course(courseName)
    return render_template("admin_courses_edit.html", course_info=course_info)

@app.route("/admin/students")
@admin_required
def admin_students():
    students = user_manager.get_all_users()
    return render_template("admin_students.html", students=students)
    

# --- FILE SERVING & APP RUN ---

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # Use a high port number and host='0.0.0.0' to avoid system permission issues
    app.run(host='0.0.0.0', port=8888, debug=True)