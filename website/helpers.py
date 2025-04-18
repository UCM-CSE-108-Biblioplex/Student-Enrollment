def get_users(request):
    try:
        page = request.args.get("page", 1)
        page = int(page)
    except:
        page = 1
    try:
        per_page = request.args.get("per_page", 50)
        per_page = int(per_page)
    except:
        per_page = 50
    
    # get matching students
    username = request.args.get("username", None)
    
    if(username):
        username = unquote(username)
        pagination = User.query.filter(
            User.username.like(f"%{username}%")
        ).paginate(
            page=page,
            per_page=per_page
        )
    else:
        pagination = User.query.paginate(page=page, per_page=per_page)
    
    users_ = pagination.items
    total_pages = pagination.pages
    total_users = pagination.total
    
    return users_, page, total_pages, total_users, per_page

def create_user(request):
    content_type = request.headers.get("Content-Type")
    if(content_type == "application/x-www-form-urlencoded"):
        data = request.form
    else:
        data = request.get_json()
    if(data is None):
        abort(Response("No request JSON", 400))
    
    is_admin = data.get("is_admin", False)
    if(is_admin and is_admin is not None):
        is_admin = is_admin.lower() in ["true", "on", "yes", "1"]

    first_name = data.get("first_name", None)
    if(not first_name):
        abort(Response("First name is required.", 400))
    middle_name = data.get("middle_name", "")
    last_name = data.get("last_name", None)
    if(not last_name):
        abort(Response("Last name is required.", 400))
    
    username = data.get("username", None)
    existing_user = User.query.filter_by(username=username).first()
    if(existing_user):
        abort(Response("Username is taken.", 400))
    if(not username):
        username = generate_username(first_name, middle_name, last_name)
    email = data.get("email", None)
    if(not email):
        abort(Response("Email is required.", 400))
    password = data.get("password", None)

    new_user = User(
        is_admin=is_admin,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        username=username,
        email=email,
        password=gph(password) if password else "needsnewpassword"
        # this password cannot collide with hashed passwords
    )
    return(new_user)

def edit_user(request):
    content_type = request.headers.get("Content-Type")
    if(content_type == "application/x-www-form-urlencoded"):
        data = request.form
    else:
        data = request.get_json()
    if(not data):
        abort(Response("No request body.", 400))
    
    # get user
    user_id = data.get("user_id", None)
    if(not user_id):
        abort(Response("User ID is required.", 400))
    target_user = User.query.get(user_id)
    if(not target_user):
        abort(Response("User not found", 404))
    
    first_name = data.get("first_name", None)
    if(first_name):
        target_user.first_name = first_name
    middle_name = data.get("middle_name", None)
    if(middle_name is not None):  # Allow empty string
        target_user.middle_name = middle_name
    last_name = data.get("last_name", None)
    if(last_name):
        target_user.last_name = last_name
    
    username = data.get("username", None)
    if(username):
        existing_user = User.query.filter_by(username=username).first()
        if(existing_user and existing_user.id != target_user.id):
            abort(Response("Username is already taken", 400))
        target_user.username = username
    generate_new_username = data.get("generate_new_username", False)
    if(generate_new_username):
        first_name = target_user.first_name
        middle_name = target_user.middle_name
        last_name = target_user.last_name
        target_user.username = generate_username(first_name, middle_name, last_name)
    email = data.get("email", None)
    if(email):
        existing_user = User.query.filter_by(email=email).first()
        if(existing_user and existing_user.id != target_user.id):
            abort(Response("Email is in use by another user.", 400))
        target_user.email = email
    
    is_admin = data.get("is_admin")
    if (is_admin is not None and is_admin.lower() in ["true", "on", "yes", "1"]):
        target_user.is_admin = is_admin.lower() in ["true", "on", "yes", "1"]
    if(not is_admin):
        target_user.is_admin = False
    
    password = data.get("password", None)
    if(password):
        target_user.password = gph(password)
    
    return(target_user)

def delete_user(request):
    content_type = request.headers.get("Content-Type")
    if(content_type == "application/x-www-form-urlencoded"):
        data = request.form
    else:
        data = request.get_json()
    if(data is None):
        abort(Response("No request JSON.", 400))
    
    user_id = data.get("user_id", None)
    if(not user_id):
        abort(Response("User ID is required.", 400))

    target_user = User.query.get(user_id)
    if(not target_user):
        abort(Response("User not found", 404))
    
    return(target_user)

def render_users(users_, current_page, total_pages, total_users, per_page):
    def parse_name(user):
        name = user.first_name + " "
        if(user.middle_name):
            name += user.middle_name
            name += " "
        name += user.last_name
        return(name)

    rows = []
    for user in users_:
        actions = render_template(
            "macros/admin/actions.html",
            model=user,
            endpoint=url_for("api_main.users"),
            model_type="user"
        )
        rows.append([
            user.id,
            user.username,
            parse_name(user),
            user.email,
            "Yes" if user.is_admin else "No",
            actions
        ])

    titles = ["ID", "Username", "Name", "Email", "Admin", "Actions"]
    return render_template(
        "macros/admin/users_content.html", 
        users=users_,
        rows=rows,
        titles=titles,
        current_page=current_page,
        total_pages=total_pages,
        total_users=total_users,
        items_per_page=per_page
    )