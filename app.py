from flask import Flask, render_template

from routes.main import main_bp


def create_app() -> Flask:
    # Serve existing frontend assets from /assets/* without moving files.
    app = Flask(__name__, static_folder="assets", static_url_path="/assets")
    app.register_blueprint(main_bp)

    @app.errorhandler(404)
    def page_not_found(_error):
        return render_template("404.html"), 404

    return app


app = create_app()
