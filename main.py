from app import app
from flask import jsonify


@app.route("/health")
def health_check():
    """Health check endpoint for Docker and monitoring"""
    return jsonify({"status": "healthy", "message": "Application is running"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
