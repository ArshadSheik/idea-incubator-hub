"""
forms.py
WTForms form definitions for Idea Incubator Hub.
All forms use Flask-WTF for CSRF protection automatically.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField,
    PasswordField, BooleanField, HiddenField, SubmitField
)
from wtforms.validators import (
    DataRequired, Length, Email, EqualTo, Optional, ValidationError
)


# ─────────────────────────────────────────
# AUTH FORMS  (used by auth blueprint — teammate's task)
# ─────────────────────────────────────────

class LoginForm(FlaskForm):
    """Login form — email + password."""
    email    = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Keep me logged in')


class RegisterForm(FlaskForm):
    """Registration form with all required user fields."""
    first_name = StringField('First name', validators=[DataRequired(), Length(1, 50)])
    last_name  = StringField('Last name',  validators=[DataRequired(), Length(1, 50)])
    username   = StringField('Username',   validators=[DataRequired(), Length(3, 20)])
    email      = StringField('Email',      validators=[DataRequired(), Email()])
    password   = PasswordField('Password', validators=[DataRequired(), Length(8, 128)])
    confirm    = PasswordField('Confirm password',
                               validators=[DataRequired(), EqualTo('password',
                               message='Passwords must match.')])

    def validate_username(self, field):
        """Reject usernames that contain spaces or special chars."""
        if not field.data.replace('_', '').replace('-', '').isalnum():
            raise ValidationError('Username can only contain letters, numbers, hyphens, and underscores.')


# ─────────────────────────────────────────
# IDEA FORMS
# ─────────────────────────────────────────

CATEGORY_CHOICES = [
    ('', '— Select a category —'),
    ('FinTech', 'FinTech'),
    ('EdTech', 'EdTech'),
    ('GreenTech', 'GreenTech'),
    ('Health', 'Health'),
    ('DevTools', 'DevTools'),
    ('Productivity', 'Productivity'),
    ('Social', 'Social'),
    ('Creator Economy', 'Creator Economy'),
    ('Other', 'Other'),
]

STAGE_CHOICES = [
    ('ideation',   'Ideation — just an idea'),
    ('validation', 'Validation — testing the concept'),
    ('building',   'Building — actively developing'),
    ('launched',   'Launched — live product'),
]

PRIVACY_CHOICES = [
    ('public',   'Public — visible to everyone'),
    ('unlisted', 'Unlisted — visible via direct link only'),
    ('private',  'Private — only you'),
]


class IdeaForm(FlaskForm):
    """Form for submitting or editing an idea."""
    title       = StringField('Title', validators=[DataRequired(), Length(3, 80)])
    summary     = StringField('One-line summary', validators=[DataRequired(), Length(10, 200)])
    description = TextAreaField('Full description', validators=[DataRequired(), Length(20, 5000)])
    category    = SelectField('Category', choices=CATEGORY_CHOICES, validators=[DataRequired()])
    stage       = SelectField('Stage', choices=STAGE_CHOICES, default='ideation')
    privacy     = SelectField('Visibility', choices=PRIVACY_CHOICES, default='public')
    tags        = StringField('Tags (comma separated)', validators=[Optional(), Length(max=200)])
    emoji       = StringField('Emoji', validators=[Optional(), Length(max=10)], default='💡')


# ─────────────────────────────────────────
# PROFILE FORMS
# ─────────────────────────────────────────

AVATAR_CHOICES = [(str(i), f'Colour {i}') for i in range(1, 7)]


class ProfileEditForm(FlaskForm):
    """Form for editing a user's own profile."""
    first_name   = StringField('First name', validators=[DataRequired(), Length(1, 50)])
    last_name    = StringField('Last name',  validators=[DataRequired(), Length(1, 50)])
    bio          = TextAreaField('Bio', validators=[Optional(), Length(max=300)])
    avatar_color = SelectField('Avatar colour', choices=AVATAR_CHOICES, default='1')
    skills       = StringField('Skills', validators=[Optional(), Length(max=200)])


# ─────────────────────────────────────────
# COMMENT / TASK FORMS
# ─────────────────────────────────────────

class CommentForm(FlaskForm):
    """Inline comment form on idea detail page."""
    body      = TextAreaField('Comment', validators=[DataRequired(), Length(1, 1000)])
    parent_id = HiddenField()   # set by JS when replying to a comment


class TaskForm(FlaskForm):
    """Form for creating or editing a Kanban task."""
    title       = StringField('Task title', validators=[DataRequired(), Length(1, 120)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    priority    = SelectField('Priority',
                              choices=[('low','Low'),('medium','Medium'),('high','High')],
                              default='medium')
    assigned_to = SelectField('Assign to', coerce=int, validators=[Optional()])

    def __init__(self, team_members=None, *args, **kwargs):
        """Pass team_members=[(id, name), ...] to populate the assignee dropdown."""
        super().__init__(*args, **kwargs)
        choices = [(0, 'Unassigned')]
        if team_members:
            choices += [(m.id, m.display_name) for m in team_members]
        self.assigned_to.choices = choices

# ─────────────────────────────────────────
# MESSAGE FORMS (for messaging system between users)
# ─────────────────────────────────────────

class MessageForm(FlaskForm):
    body = TextAreaField(
        "Message",
        validators=[
            DataRequired(message="Message cannot be empty."),
            Length(max=1000, message="Message must be 1000 characters or less."),
        ],
    )
    submit = SubmitField("Send")