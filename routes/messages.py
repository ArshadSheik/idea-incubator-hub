from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, or_

from forms import MessageForm
from models.models import DirectMessage, Notification, User, db

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")


def _build_conversations():
    messages = (
        DirectMessage.query
        .filter(
            or_(
                DirectMessage.sender_id == current_user.id,
                DirectMessage.recipient_id == current_user.id,
            )
        )
        .order_by(DirectMessage.created_at.desc())
        .all()
    )

    latest_by_user = {}

    for message in messages:
        other_user_id = (
            message.recipient_id
            if message.sender_id == current_user.id
            else message.sender_id
        )

        if other_user_id not in latest_by_user:
            latest_by_user[other_user_id] = message

    user_ids = list(latest_by_user.keys())
    users = {
        user.id: user
        for user in User.query.filter(User.id.in_(user_ids)).all()
    } if user_ids else {}

    conversations = []

    for other_user_id, latest_message in latest_by_user.items():
        other_user = users.get(other_user_id)
        if not other_user:
            continue

        unread_count = (
            DirectMessage.query
            .filter_by(
                sender_id=other_user_id,
                recipient_id=current_user.id,
                is_read=False,
            )
            .count()
        )

        conversations.append(
            {
                "user": other_user,
                "latest_message": latest_message,
                "unread_count": unread_count,
            }
        )

    return conversations


def _search_people(query):
    if not query:
        return []

    q = f"%{query}%"
    return (
        User.query
        .filter(
            User.id != current_user.id,
            or_(
                User.username.ilike(q),
                User.first_name.ilike(q),
                User.last_name.ilike(q),
            )
        )
        .limit(8)
        .all()
    )


@messages_bp.route("/", defaults={"username": None}, methods=["GET"])
@messages_bp.route("/<username>", methods=["GET", "POST"])
@login_required
def inbox(username):
    form = MessageForm()
    search_query = request.args.get("q", "").strip()

    conversations = _build_conversations()
    search_results = _search_people(search_query)

    selected_user = None
    thread_messages = []
    can_message = False

    if username:
        selected_user = User.query.filter_by(username=username).first_or_404()

        if selected_user.id == current_user.id:
            flash("You cannot message yourself.", "info")
            return redirect(url_for("messages.inbox"))

        can_message = current_user.follows(selected_user)

        thread_messages = (
            DirectMessage.query
            .filter(
                or_(
                    and_(
                        DirectMessage.sender_id == current_user.id,
                        DirectMessage.recipient_id == selected_user.id,
                    ),
                    and_(
                        DirectMessage.sender_id == selected_user.id,
                        DirectMessage.recipient_id == current_user.id,
                    ),
                )
            )
            .order_by(DirectMessage.created_at.asc())
            .all()
        )

        DirectMessage.query.filter_by(
            sender_id=selected_user.id,
            recipient_id=current_user.id,
            is_read=False,
        ).update({"is_read": True})

        Notification.query.filter_by(
            user_id=current_user.id,
            type="message",
            link=url_for("messages.inbox", username=selected_user.username),
            is_read=False,
        ).update({"is_read": True}, synchronize_session=False)

        db.session.commit()

    if request.method == "POST":
        if not selected_user:
            flash("Please select a user first.", "warning")
            return redirect(url_for("messages.inbox"))

        if not current_user.follows(selected_user):
            flash("Follow this user to send messages.", "warning")
            return redirect(url_for("messages.inbox", username=selected_user.username))

        if form.validate_on_submit():
            body = form.body.data.strip()

            message = DirectMessage(
                sender_id=current_user.id,
                recipient_id=selected_user.id,
                body=body,
            )
            db.session.add(message)

            notification = Notification(
                user_id=selected_user.id,
                type="message",
                message=f"{current_user.display_name} sent you a new message.",
                link=url_for("messages.inbox", username=current_user.username),
            )
            db.session.add(notification)

            db.session.commit()

            return redirect(url_for("messages.inbox", username=selected_user.username))

    return render_template(
        "messages.html",
        conversations=conversations,
        search_results=search_results,
        search_query=search_query,
        selected_user=selected_user,
        thread_messages=thread_messages,
        can_message=can_message,
        form=form,
    )