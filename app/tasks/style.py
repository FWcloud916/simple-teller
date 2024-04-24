# type: ignore
import inspect

if not hasattr(inspect, "getargspec"):
    inspect.getargspec = inspect.getfullargspec

from invoke import task


@task
def black_check(ctx):
    """Check style through black"""
    ctx.run("black --check app/.")


@task
def black_change(ctx):
    """Reformat style through black"""
    ctx.run("black app/.")


@task
def isort_check(ctx):
    """Check style through isort"""
    ctx.run("isort --atomic --check-only app/.")


@task
def isort_change(ctx):
    """Reformat style through isort"""
    ctx.run("isort --atomic app/.")


@task
def pylint(ctx):
    """Check style through pylint"""
    ctx.run("pylint app/**/*.py")


@task
def mypy(ctx):
    """Check style through mypy"""
    ctx.run("mypy app")


@task(pre=[black_check, isort_check, pylint, mypy])
def check(ctx):
    """check all coding style"""


@task(pre=[black_change, isort_change])
def reformat(ctx):
    """check all coding style"""
