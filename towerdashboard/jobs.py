import json

from redis import Redis

from towerdashboard import app as APP


def refresh_github_branches():
    app = APP.create_app(start_background_scheduled_jobs=False)
    app.cache.delete_memoized(app.github.get_branches)
    app.github.get_branches()
