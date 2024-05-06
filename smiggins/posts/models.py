from django.db import models

class User(models.Model):
    user_id  = models.IntegerField(primary_key=True, unique=True)
    username = models.CharField(max_length=300, unique=True)
    token    = models.CharField(max_length=64, unique=True)

    # Admin level
    # 0 - Regular user
    # 1 - Ability to delete any post
    # 2 - Ability to delete any account
    # 3 - Ability to add badges to accounts and create new badges
    # 4 - Full access to modify anything in the database except for admin levels
    # 5 - Ability to add anyone as an admin of any level, including level 5. This is automatically given to the owner specified in _settings.py
    admin_level = models.IntegerField(default=0)

    display_name = models.CharField(max_length=300)
    bio       = models.CharField(max_length=65536, default="", blank=True)
    pronouns  = models.CharField(max_length=2, default="__")
    theme     = models.CharField(max_length=30)
    color     = models.CharField(max_length=7)
    color_two = models.CharField(max_length=7, default="#000000", blank=True)
    gradient  = models.BooleanField(default=False)
    private   = models.BooleanField()

    following = models.JSONField(default=list, blank=True)
    followers = models.JSONField(default=list, blank=True)
    blocking  = models.JSONField(default=list, blank=True)
    badges    = models.JSONField(default=list, blank=True)
    notifications = models.JSONField(default=list, blank=True)
    read_notifs = models.BooleanField(default=True)

    pinned   = models.IntegerField(default=0)
    posts    = models.JSONField(default=list, blank=True)
    comments = models.JSONField(default=list, blank=True)
    likes    = models.JSONField(default=list, blank=True) # list[list[id: int, is_comment: bool]]

    def __str__(self):
        return f"({self.user_id}) {self.username}"

class Post(models.Model):
    post_id   = models.IntegerField(primary_key=True)
    content   = models.TextField(max_length=65536)
    creator   = models.IntegerField()
    timestamp = models.IntegerField()
    quote     = models.IntegerField(default=0)
    quote_is_comment = models.BooleanField(default=False)

    likes    = models.JSONField(default=list, blank=True)
    comments = models.JSONField(default=list, blank=True)
    quotes   = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"({self.post_id}) {self.content}"

class Comment(models.Model):
    comment_id = models.IntegerField(primary_key=True, unique=True)
    content    = models.TextField(max_length=65536)
    creator    = models.IntegerField()
    timestamp  = models.IntegerField()
    parent     = models.IntegerField(default=0)
    parent_is_comment = models.BooleanField(default=False)

    likes    = models.JSONField(default=list, blank=True)
    comments = models.JSONField(default=list, blank=True)
    quotes   = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"({self.comment_id}) {self.content}"

class Badge(models.Model):
    name     = models.CharField(max_length=64, primary_key=True, unique=True)
    svg_data = models.CharField(max_length=65536)
    users    = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.name} ({', '.join([str(i) for i in self.users]) or 'No users'})"

class Notification(models.Model):
    notif_id  = models.IntegerField(primary_key=True, unique=True)
    timestamp = models.IntegerField()
    read      = models.BooleanField(default=False)

    # The type of the event that caused the notification. Can be:
    # - comment (commenting on your post)
    # - quote_p (your post being quoted)
    # - quote_c (your comment being quoted)
    # - ping_p (ping from a post)
    # - ping_c (ping from a comment)
    event_type = models.CharField(max_length=7)

    # The id for whatever happened.
    # - comment: it would be a comment id
    # - quote: the post id of the quote
    # - ping_p: it would be the post the ping came from
    # - ping_c: it would be the comment id from where the ping came from
    event_id = models.IntegerField()

    # The user object for who the notification is for
    is_for = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"({'' if self.read else 'un'}read) {self.event_type} ({self.event_id}) for {self.is_for.username}"
