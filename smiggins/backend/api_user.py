# For API functions that are user-specific, like settings, following, etc.

from ._settings import *
from .packages  import *
from .schema    import *
from .helper    import *

def api_account_signup(request, data: accountSchema) -> tuple | dict:
    # Called when someone requests to follow another account.

    if not ensure_ratelimit("api_account_signup", request.META.get("REMOTE_ADDR")):
        return 429, {
            "valid": False,
            "reason": "Ratelimited"
        }

    username = data.username.lower().replace(" ", "")
    password = data.password.lower()

    # e3b0c44... is the sha256 hash for an empty string
    if len(password) != 64 or password == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855":
        return {
            "valid": False,
            "reason": "Invalid Password"
        }

    for i in password:
        if i not in "abcdef0123456789":
            return {
                "valid": False,
                "reason": "Invalid Password"
            }

    user_valid = validate_username(username, existing=False)
    if user_valid == 1:
        create_api_ratelimit("api_account_signup", API_TIMINGS["signup successful"], request.META.get('REMOTE_ADDR'))

        token = generate_token(username, password)
        user = User(
            username=username,
            token=token,
            display_name=username,
            theme="dark",
            color=DEFAULT_BANNER_COLOR,
            private=False,
            following=[],
            followers=[],
            posts=[],
        )
        user.save()

        user = User.objects.get(username=username)

        user.following = [user.user_id]
        user.save()

        return {
            "valid": True,
            "token": token
        }

    create_api_ratelimit("api_account_signup", API_TIMINGS["signup unsuccessful"], request.META.get('REMOTE_ADDR'))

    if user_valid == -1:
        return {
            "valid": False,
            "reason": "Username taken."
        }

    elif user_valid == -2:
        return {
            "valid": False,
            "reason": "Username can only use A-Z, 0-9, underscores, and hyphens."
        }

    return {
        "valid": False,
        "reason": f"Username must be between 1 and {MAX_USERNAME_LENGTH} characters in length."
    }

def api_account_login(request, data: accountSchema) -> tuple | dict:
    # Called when someone attempts to log in.

    if not ensure_ratelimit("api_account_login", request.META.get("REMOTE_ADDR")):
        return 429, {
            "valid": False,
            "reason": "Ratelimited"
        }

    username = data.username.lower()
    password = data.password
    token = generate_token(username, password)

    if validate_username(username) == 1:
        if token == User.objects.get(username=username).token:
            create_api_ratelimit("api_account_login", API_TIMINGS["login successful"], request.META.get('REMOTE_ADDR'))
            return {
                "valid": True,
                "token": token
            }

        else:
            create_api_ratelimit("api_account_login", API_TIMINGS["login unsuccessful"], request.META.get('REMOTE_ADDR'))
            return {
                "valid": False,
                "reason": "Invalid password."
            }

    else:
        create_api_ratelimit("api_account_login", API_TIMINGS["login unsuccessful"], request.META.get('REMOTE_ADDR'))
        return {
            "valid": False,
            "reason": f"Account with username {username} doesn't exist."
        }

def api_user_settings_theme(request, data: themeSchema) -> tuple | dict:
    # Called when the user changes their theme.

    token = request.COOKIES.get('token')
    theme = data.theme.lower()

    if theme.lower() not in ["light", "gray", "dark", "black"]:
        return 400, {
            "success": False,
            "reason": "That's not a vailid theme, idiot.",
        }

    user = User.objects.get(token=token)
    user.theme = theme
    user.save()

    return {
        "success": True
    }

def api_user_settings(request, data: settingsSchema) -> tuple | dict:
    # Called when someone saves their settings

    token = request.COOKIES.get('token')

    color = data.color.lower()
    color_two = data.color_two.lower()
    displ_name = trim_whitespace(data.displ_name, True)
    bio = trim_whitespace(data.bio, True)

    if (len(displ_name) > MAX_DISPL_NAME_LENGTH or len(displ_name) < 1) or (len(bio) > MAX_BIO_LENGTH):
        return 400, {
            "success": False,
            "reason": f"Invalid name length. Must be between 1 and {MAX_DISPL_NAME_LENGTH} characters after minifying whitespace."
        }

    if color[0] != "#" or len(color) != 7 or color_two[0] != "#" or len(color_two) != 7:
        return 400, {
        "success": False,
        "reason": "Color very no tasty"
    }

    for i in color[1::]:
        if i not in "abcdef0123456789":
            return 400, {
                "success": False,
                "reason": "Color no tasty"
            }

    for i in color_two[1::]:
        if i not in "abcdef0123456789":
            return 400, {
                "success": False,
                "reason": "Color no yummy"
            }

    user = User.objects.get(token=token)

    user.color = color
    user.color_two = color_two
    user.gradient = data.is_gradient
    user.private = data.priv
    user.display_name = displ_name
    user.bio = bio

    user.save()

    return {
        "success": True
    }

def api_user_follower_add(request, data: userSchema) -> tuple | dict:
    # Called when someone requests to follow another account.

    token = request.COOKIES.get('token')
    username = data.username.lower()

    if not validate_username(username):
        return 400, {
            "valid": False,
            "reason": f"Account with username {username} doesn't exist."
        }

    user = User.objects.get(token=token)
    followed = User.objects.get(username=username)
    if followed.user_id not in user.following:
        user.following.append(followed.user_id)
        user.save()

    if user.user_id not in (followed.followers or []):
        followed.followers.append(user.user_id) # type: ignore
        followed.save()

    return 201, {
        "success": True
    }

def api_user_follower_remove(request, data: userSchema) -> tuple | dict:
    # Called when someone requests to unfollow another account.

    token = request.COOKIES.get('token')
    username = data.username.lower()

    if not validate_username(username):
        return 400, {
            "valid": False,
            "reason": f"Account with username {username} doesn't exist."
        }

    user = User.objects.get(token=token)
    followed = User.objects.get(username=username)
    if user.user_id != followed.user_id:
        if followed.user_id in user.following :
            user.following.remove(followed.user_id)
            user.save()

        if user.user_id in (followed.followers or []):
            followed.followers.remove(user.user_id) # type: ignore
            followed.save()
    else:
        return 400, {
            "success": False
        }

    return 201, {
        "success": True
    }

def api_user_delete(request, data: adminAccountSchema) -> tuple | dict:
    # Called when someone deletes an account.

    token = request.COOKIES.get('token')
    identifier = data.identifier
    use_id = data.use_id

    try:
            if use_id:
                account = User.objects.get(user_id=int(identifier))
            else:
                account = User.objects.get(username=identifier)
    except User.DoesNotExist:
            return 404, {
                "success": False,
                "reason": "User not found!"
            }

    try:
        user = User.objects.get(token=token)
    except User.DoesNotExist:
        return 404, {
            "success": False
        }

    if account.user_id == user.user_id or user.user_id == OWNER_USER_ID or user.admin_level >= 2:
        for post_id in account.posts:
            try:
                post = Post.objects.get(post_id=post_id)
            except Post.DoesNotExist:
                pass

            if post.quote:
                try:
                    quoted_post = (Comment if post.quote_is_comment else Post).objects.get(pk=post.quote)
                    quoted_post.quotes.remove(post.post_id) # type: ignore
                    quoted_post.save()
                except Post.DoesNotExist:
                    pass
                except Comment.DoesNotExist:
                    pass

            post.delete()

        for followed_id in account.following:
            if followed_id == account.user_id:
                continue

            followed = User.objects.get(user_id=followed_id)
            followed.followers.remove(account.user_id) # type: ignore
            followed.save()

        for follower_id in account.followers:
            if follower_id == account.user_id:
                continue

            follower = User.objects.get(user_id=follower_id)
            follower.following.remove(account.user_id) # type: ignore
            follower.save()

        account.delete()

        return {
            "success": True
        }

    return 400, {
        "success": False
    }
