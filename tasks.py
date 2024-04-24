from invoke import Collection

from app.tasks import style

ns = Collection()
ns.add_collection(style)
