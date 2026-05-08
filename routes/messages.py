from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import and_, or_

from forms import MessageForm
from models.models import DirectMessage, User, db, Notification

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")


@messages_bp.route("/")
@login_required
def inbox():
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

    return render_template("messages_inbox.html", conversations=conversations)


@messages_bp.route("/<username>", methods=["GET", "POST"])
@login_required
def thread(username):
    other_user = User.query.filter_by(username=username).first_or_404()

    if other_user.id == current_user.id:
        flash("You cannot message yourself.", "info")
        return redirect(url_for("messages.inbox"))

    form = MessageForm()

    if form.validate_on_submit():
        body = form.body.data.strip()
        
        message = DirectMessage(
        sender_id=current_user.id,
        recipient_id=other_user.id,
        body=body,
        )
        db.session.add(message)
        
        notification = Notification(
        user_id=other_user.id,
        type="message",
        message=f"{current_user.display_name} sent you a new message.",
        link=url_for("messages.thread", username=current_user.username),
        )
        db.session.add(notification)
        
        db.session.commit()
        return redirect(url_for("messages.thread", username=other_user.username))

    DirectMessage.query.filter_by(
        sender_id=other_user.id,
        recipient_id=current_user.id,
        is_read=False,
    ).update({"is_read": True})

    db.session.commit()

    thread_messages = (
        DirectMessage.query
        .filter(
            or_(
                and_(
                    DirectMessage.sender_id == current_user.id,
                    DirectMessage.recipient_id == other_user.id,
                ),
                and_(
                    DirectMessage.sender_id == other_user.id,
                    DirectMessage.recipient_id == current_user.id,
                ),
            )
        )
        .order_by(DirectMessage.created_at.asc())
        .all()
    )

    return render_template(
        "messages_thread.html",
        other_user=other_user,
        messages=thread_messages,
        form=form,
    )